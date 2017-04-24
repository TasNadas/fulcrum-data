import fulcrum, sys, json, os, codecs, string, math
import httplib2 as http
from fulcrum import Fulcrum

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

uname = "tas@nadas.org"
pw    = "Nadas4CH!"
streettoadd = 'Delaware'

uri   = 'http://api.fulcrumapp.com'
DEBUG = False


csvfldr = r'G:\Councilman_TNadas_2017\2017_Councilman\shapefiles\FulcrumJoin'
csvname = "fulcrumjoin"

class User:
    def __init__(self, user=None, pw=None):
        self.user = user
        self.password = pw

class Project:
    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description


def log(message):
    print message
    f = file(sys.argv[0]+".log", 'a')
    f.write("%s\n" % message)
    f.close()
def GetData(path, headers=None, auth=None):
    target = urlparse(uri + path)
    method = 'GET'
    body = ''

    h = http.Http()
    if auth:
        h.add_credentials(auth.user, auth.password)

    return PutData(path, '', headers, "GET", h)


def PutData(path, body, headers, method="PUT", h=None):
    target = urlparse(uri + path)
    if not h:
        h = http.Http()
    response, content = h.request(
        target.geturl(),
        method,
        body,
        headers)

    if DEBUG:
        log(method + " " + target.geturl())
        for i in response:
            log("\t" + i.ljust(20) + response[i])

    if response['status'] == '204':
        content = '{"status": "204: No content returned, OK"}'
    try:
        data = json.loads(content)
    except ValueError as err:
        log("target: %s" % target.geturl())
        log("content:%s" % content)
        log("error:  %s" % Dump(response))
        raise err
    return data


def Dump(data):
    return json.dumps(data ,sort_keys=True, indent=4, separators=(',', ': '))

def delrecords(form_id, header, fulcrum):
    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # 'project_id' = '86d4b7cd-4e8d-4260-b69c-747301c06835' = To Visit
        # 'project_id' = 'ab594e47-7bc8-4174-95ef-86e7e3479ead' = All Residents
        if row['project_id'] == '87245230-86cb-43f5-9d45-8e921307b03d':
            fulcrum.records.delete(row[u'id'])


def resetrecordstooneproject(form_id, header, fulcrum):
    fields = {}

    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])

    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # 'project_id' = '86d4b7cd-4e8d-4260-b69c-747301c06835' = To Visit
        # 'project_id' = 'ab594e47-7bc8-4174-95ef-86e7e3479ead' = All Residents
        update_record = row
        update_record['project_id'] = 'ab594e47-7bc8-4174-95ef-86e7e3479ead'
        fulcrum.records.update(row[u'id'], update_record)

def distance_between_gps_in_km(lat1, lon1, lat2, lon2):
    earth_radius = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    # Haversine formula
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
    c = math.atan2(math.sqrt(a), math.sqrt(1-a))
    return earth_radius * c




def create_street_name_array(form_id, headers, fulcrum):
    street_names = set()
    fields = {}

    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)  #fulcrum.records.search(url_params={'form_id': form_id})
    getFields(form_fields['form'])
    form_found = fulcrum.records.search(url_params={'form_id': form_id})

    # Get this to work without getFields prz

    for record in form_found['records']:
        street_name = record['form_values'][fields['street_address']]
        street_name = street_name.split(" ")[1]
        street_names.add(street_name)
    return street_names

def find_street_length(form_id, headers, fulcrum, street_name):
    fields = {}
    houses_on_this_street = []
    even_houses = []
    odd_houses = []
    count = 0
    walking_speed = 12
    talking_time = 5
    house_count = 0

    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])
    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        try:
            street = row['form_values'][fields['street_address']]
            try:
                street = street.split(" ")[1]
            except:
                street = ""
        except:
            street = ""
        if (street == street_name):
            #Add this record to the list to be sorted
            houses_on_this_street.append(row)

    # First, split the array into even and odd street numbers
    # This is done because you will be walking down one side of the street at a time
    for house in houses_on_this_street:
        try:
            street_num = house['form_values'][fields['street_address']].split(" ")[0]
        except:
            street_num = ""
        street_num_i = int(street_num)
        if (street_num_i % 2 == 0):
            even_houses.append(house)
        else:
            odd_houses.append(house)
        house_count += 1

    # Next, sort the houses by address number
    # houses_on_this_street = sorted(houses_on_this_street, key=lambda number: number['form_values'][fields['street_address']])
    even_houses = sorted(even_houses, key=lambda number: number['form_values'][fields['street_address']])
    odd_houses = sorted(odd_houses, key=lambda number: number['form_values'][fields['street_address']])
    # print even_houses
    # print "ODD"
    # print odd_houses

    # Then calculate the distance between houses on each side of the street
    total_distance = 0
    count = 0
    house_count = len(even_houses)
    while (count < house_count - 1):
        first_house_lat = even_houses[count]['latitude']
        first_house_lon = even_houses[count]['longitude']
        next_house_lat = even_houses[count + 1]['latitude']
        next_house_lon = even_houses[count + 1]['longitude']
        total_distance += distance_between_gps_in_km(first_house_lat, first_house_lon, next_house_lat, next_house_lon)
        count += 1

    count = 0
    house_count = len(odd_houses)
    while (count < house_count - 1):
        first_house_lat = odd_houses[count]['latitude']
        first_house_lon = odd_houses[count]['longitude']
        next_house_lat = odd_houses[count + 1]['latitude']
        next_house_lon = odd_houses[count + 1]['longitude']
        total_distance += distance_between_gps_in_km(first_house_lat, first_house_lon, next_house_lat, next_house_lon)
        count += 1

    # Next we calculate the total time it would take to traverse
    # this street based on the walking speed and amount of
    # time spent talking at each house.  This is converting
    # from kilometers into minutes to make things easier

    total_time = (total_distance * walking_speed) + (house_count * talking_time)

    return total_time

def filter_all_residents(form_id, headers, fulcrum):
    fields = {}
    filtered_records = []
    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])

    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # 'project_id' = '86d4b7cd-4e8d-4260-b69c-747301c06835' = To Visit
        # 'project_id' = 'ab594e47-7bc8-4174-95ef-86e7e3479ead' = All Residents

        update = False
        update_record = row
        # if row['project_id'] != '86d4b7cd-4e8d-4260-b69c-747301c06835' and row['project_id'] is not None:
        #     print row['form_values'][fields['street_address']]
        #     print row['project_id']
        # if row['project_id'] == '86d4b7cd-4e8d-4260-b69c-747301c06835':
        numres = 0
        resarry = []
        numvoters = 0
        notapt = False

        for i in row['form_values'][fields['residents']]:
            numres += 1
            # print i
            try:
                resarry.append(i['form_values'][fields['apartment']])
            except:
                notapt = True
            try:
                party = i['form_values'][fields['party']]
            except:
                party = ""
            try:
                y2015 = i['form_values'][fields['g201511']]
            except:
                y2015 = ""
            try:
                y2014 = i['form_values'][fields['g201411']]
            except:
                y2014 = ""
            try:
                y2016 = i['form_values'][fields['g201611']]
            except:
                y2016 = ""
            try:
                birth = i['form_values'][fields['birth_year']]
            except:
                birth = ""
            if (y2016 == "Y" or y2015 == "Y" or y2014 == "Y"):
                numvoters += 1

        residentset = []
        if notapt == False and len(resarry) > 0:
            residentset = []
            for res in resarry:
                if len(residentset) == 0:
                    residentset.append(res)
                else:
                    alreadyadded = False
                    for resset in residentset:
                        if resset == res:
                            alreadyadded = True
                    if not alreadyadded:
                        residentset.append(res)
        else:
            residentset = []
        if len(residentset) <= 3:
            # print numvoters
            if numvoters > 0:
                update = True

        if update == True:
            filtered_records.append(row)

        print
        print filtered_records

    return filtered_records

def project_update(form_id, headers, fulcrum, street):
    fields = {}
    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])

    # Democrats
    # Voted in 2015, 2014, or 2013
    # Under 45
    # fewer than 2 or 3 units

    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # 'project_id' = '86d4b7cd-4e8d-4260-b69c-747301c06835' = To Visit
        # 'project_id' = 'ab594e47-7bc8-4174-95ef-86e7e3479ead' = All Residents

        update = False
        update_record = row
        # if row['project_id'] != '86d4b7cd-4e8d-4260-b69c-747301c06835' and row['project_id'] is not None:
        #     print row['form_values'][fields['street_address']]
        #     print row['project_id']
        # if row['project_id'] == '86d4b7cd-4e8d-4260-b69c-747301c06835':
        numres = 0
        resarry = []
        numvoters = 0
        notapt = False
        # try:
        # try:
        #     residents = row['form_values'][fields['residents']]
        # except:
        #     update_record['project_id'] = '87245230-86cb-43f5-9d45-8e921307b03d' # No Residents
        #     fulcrum.records.update(row[u'id'], update_record)
        try:
            street = row['form_values'][fields['street_address']]
            try:
                street = street.split(" ")[1]
            except:
                street = ""
        except:
            street = ""

        for i in row['form_values'][fields['residents']]:
            numres += 1
            # print i
            try:
                resarry.append(i['form_values'][fields['apartment']])
            except:
                notapt = True
            try:
                party = i['form_values'][fields['party']]
            except:
                party = ""
            try:
                y2015 = i['form_values'][fields['g201511']]
            except:
                y2015 = ""
            try:
                y2014 = i['form_values'][fields['g201411']]
            except:
                y2014 = ""
            try:
                y2016 = i['form_values'][fields['g201611']]
            except:
                y2016 = ""
            try:
                birth = i['form_values'][fields['birth_year']]
            except:
                birth = ""
            if (y2016 == "Y" or y2015 == "Y" or y2014 == "Y") and string.upper(street) == string.upper(streettoadd):
                numvoters += 1

        residentset = []
        if notapt == False and len(resarry) > 0:
            residentset = []
            for res in resarry:
                if len(residentset) == 0:
                    residentset.append(res)
                else:
                    alreadyadded = False
                    for resset in residentset:
                        if resset == res:
                            alreadyadded = True
                    if not alreadyadded:
                        residentset.append(res)
        else:
            residentset = []
        if len(residentset) <= 3:
            # print numvoters
            if numvoters > 0:
                update = True

        if update == True:
            # update_record['form_values'][fields['comments']] = 'updated'
            update_record['project_id'] = '4203567b-dd5b-4e19-855e-0a7a63a2084e'
            fulcrum.records.update(row[u'id'], update_record)
        # except:
        #     print row['form_values'][fields['street_address']] + " missing residents"











def recordupdate(form_id, headers, fulcrum):
    fields = {}
    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])

    # Democrats
    # Voted in 2015, 2014, or 2013
    # Under 45
    # fewer than 2 or 3 units

    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # 'project_id' = '86d4b7cd-4e8d-4260-b69c-747301c06835' = To Visit
        # 'project_id' = 'ab594e47-7bc8-4174-95ef-86e7e3479ead' = All Residents

        update = False
        update_record = row
        # if row['project_id'] != '86d4b7cd-4e8d-4260-b69c-747301c06835' and row['project_id'] is not None:
        #     print row['form_values'][fields['street_address']]
        #     print row['project_id']
        # if row['project_id'] == '86d4b7cd-4e8d-4260-b69c-747301c06835':
        numres = 0
        resarry = []
        numvoters = 0
        notapt = False
        # try:
        # try:
        #     residents = row['form_values'][fields['residents']]
        # except:
        #     update_record['project_id'] = '87245230-86cb-43f5-9d45-8e921307b03d' # No Residents
        #     fulcrum.records.update(row[u'id'], update_record)
        try:
            street = row['form_values'][fields['street_address']]
            try:
                street = street.split(" ")[1]
            except:
                street = ""
        except:
            street = ""

        for i in row['form_values'][fields['residents']]:
            numres += 1
            # print i
            try:
                resarry.append(i['form_values'][fields['apartment']])
            except:
                notapt = True
            try:
                party = i['form_values'][fields['party']]
            except:
                party = ""
            try:
                y2015 = i['form_values'][fields['g201511']]
            except:
                y2015 = ""
            try:
                y2014 = i['form_values'][fields['g201411']]
            except:
                y2014 = ""
            try:
                y2016 = i['form_values'][fields['g201611']]
            except:
                y2016 = ""
            try:
                birth = i['form_values'][fields['birth_year']]
            except:
                birth = ""
            if (y2016 == "Y" or y2015 == "Y" or y2014 == "Y") and string.upper(street) == string.upper(streettoadd):
                numvoters += 1

        residentset = []
        if notapt == False and len(resarry) > 0:
            residentset = []
            for res in resarry:
                if len(residentset) == 0:
                    residentset.append(res)
                else:
                    alreadyadded = False
                    for resset in residentset:
                        if resset == res:
                            alreadyadded = True
                    if not alreadyadded:
                        residentset.append(res)
        else:
            residentset = []
        if len(residentset) <= 3:
            # print numvoters
            if numvoters > 0:
                update = True

        if update == True:
            # update_record['form_values'][fields['comments']] = 'updated'
            update_record['project_id'] = '4203567b-dd5b-4e19-855e-0a7a63a2084e'
            fulcrum.records.update(row[u'id'], update_record)
        # except:
        #     print row['form_values'][fields['street_address']] + " missing residents"


def exporttocsv(tbl):
    fname = os.path.join(str(csvfldr), csvname + ".csv")

    if os.path.exists(fname): os.remove(fname)

    csvfile = codecs.open(fname, 'w', 'utf-8')

    csvfile.write("\"Street_Name\",\"FulcrumID")
    csvfile.write("\"\n")

    for row in tbl:
        csvfile.write("\"" + row[0] + "\",\"" + str(row[1]))
        csvfile.write("\"\n")

    csvfile.write("\"\n")

    csvfile.close()


if __name__ == '__main__':
    full_path = sys.argv[0]

    api_key = os.environ['FULCRUM_API_KEY']

    fulcrum = Fulcrum(key=api_key)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
        'X-ApiToken': api_key
    }

    street_times = []
    filtered_street_times = []
    count = 0
    allotted_time_per_street = 60

    form_name = 'CH Voters 2017'
    form_found = fulcrum.forms.search(url_params={'name': form_name})
    project_name = 'All Residents'
    project_found = fulcrum.projects.search(url_params={'name': project_name})

    form_id = ''
    for form in form_found['forms']:
        if form['name'] == form_name:
            form_id = form['id']

    for project in project_found['projects']:
        print project['name']
        print project['id']

    # First we need to filter all of the residences into the voters
    # that we care about the most.  This will create a new form that
    # only contains residences where:
    # A resident voted in 2016, 2015, or 2014
    # The residence is not an apartment

    #fulcrum.forms.create(filter_all_residents(form_id, headers, fulcrum))
    index = 1
    for i in
    new_project = {}
    new_project['name'] = 'Hour ' + i

    wrapper = {}
    wrapper['project'] = new_project


    newer_project = fulcrum.projects.create(wrapper)

    print "New project created?"




    # street_name_array = create_street_name_array(form_id, headers, fulcrum)
    # #print street_name_array
    # #street_length_km = find_street_length(form_id, headers, fulcrum, street_name_array[0])
    # #print street_length_km
    # num_streets = len(street_name_array)
    # # while(count < num_streets):
    # #     distance_array.append(find_street_length(form_id, headers, fulcrum, street_name_array[count]))
    # #     print distance_array[count]
    # #     print count
    # #     print num_streets
    # #     count += 1
    #
    # count = 1
    # for street in street_name_array:
    #     street_times.append(find_street_length(form_id, headers, fulcrum, street))
    #     print street, "is", count, "of", num_streets
    #     count += 1
    #
    #
    #
    # print street_times
    #
    # # Next sort the street names by distance
    # streets_and_times = zip(street_times, street_name_array)
    # for street_time in streets_and_times:
    #     # We only care about streets that can be traversed in less than our allotted time
    #     if street_time[0] < allotted_time_per_street:
    #         filtered_street_times.append(street_time)
    #
    #
    # print filtered_street_times
    #
    # #streets_time_sorted = [x for (y, x) in sorted(zip(street_times, street_name_array))]
    # streets_time_sorted = [x for (y, x) in sorted(filtered_street_times)]
    #
    # print streets_time_sorted




    # Use street name array to create another array that has total distance traversed on that street
    # Then sort that and put all of the streets with less than X distance into a Usable array
    # Then see how many residences are there
    # If > 3360, filter more

    # print form_ida

    # delrecords(form_id, headers, fulcrum)
    #recordupdate(form_id, headers, fulcrum)
    # resetrecordstooneproject(form_id, headers, fulcrum)
    # expo1rttocsv(tbl)

    print "DONE!"


  File "C:/Users/Doug Glaser/PycharmProjects/Campaign2017/Create_Filtered_Form.py", line 595, in <module>
    fulcrum.projects.create(new_project)
  File "C:\Python27\lib\site-packages\fulcrum\mixins.py", line 16, in create
    api_resp = self.call('post', self.path, data=obj, extra_headers={'Content-Type': 'application/json'})
  File "C:\Python27\lib\site-packages\fulcrum\api\__init__.py", line 45, in call
    kwargs['data'] = json.dumps(data)
  File "C:\Python27\lib\json\__init__.py", line 244, in dumps
    return _default_encoder.encode(obj)
  File "C:\Python27\lib\json\encoder.py", line 207, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "C:\Python27\lib\json\encoder.py", line 270, in iterencode
    return _iterencode(o, 0)
  File "C:\Python27\lib\json\encoder.py", line 184, in default
    raise TypeError(repr(o) + " is not JSON serializable")
TypeError: <__main__.Project instance at 0x03C140A8> is not JSON serializable