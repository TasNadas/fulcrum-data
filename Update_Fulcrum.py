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
filtered_project_id = '4203567b-dd5b-4e19-855e-0a7a63a2084e'
visit_project_id = '86d4b7cd-4e8d-4260-b69c-747301c06835'

uri   = 'http://api.fulcrumapp.com'
DEBUG = False


csvfldr = r'G:\Councilman_TNadas_2017\2017_Councilman\shapefiles\FulcrumJoin'
csvname = "fulcrumjoin"

class User:
    def __init__(self, user=None, pw=None):
        self.user = user
        self.password = pw


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

def find_street_length(form_id, headers, fulcrum, street_name, project_id):
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
        if (street == street_name and row['project_id'] == project_id):
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

def filter_all_residents(form_id, headers, fulcrum, targeted_id):
    fields = {}
    filtered_records = []
    filter_count = 0
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
            update_record['form_values'][fields['comments']] = 'filtered'
            update_record['project_id'] = targeted_id
            fulcrum.records.update(row[u'id'], update_record)
            print "Filter count is ", filter_count
            filter_count += 1

def update_to_visit(form_id, headers, fulcrum, streets):
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
            form_street = row['form_values'][fields['street_address']]
            try:
                form_street = form_street.split(" ")[1]
            except:
                form_street = ""
        except:
            form_street = ""

        for timed_street in streets:
            if form_street == timed_street:
                update = True

        if update == True:
            # update_record['form_values'][fields['comments']] = 'updated'
            update_record['project_id'] = visit_project_id
            fulcrum.records.update(row[u'id'], update_record)
        # except:
        #     print row['form_values'][fields['street_address']] + " missing residents"

def create_hourly_projects(form_id, headers, fulcrum, streets, project_id):
    fields = {}
    new_project = {}
    wrapper = {}
    count = 0
    num_streets = len(streets)
    found_street = {}
    found_street['name'] = 'default'
    project_found = False


    def getFields(data):
        if "elements" in data:
            for e in data["elements"]:
                getFields(e)
                fields[e['data_name']] = e['key']

    form_fields = GetData('/api/v2/forms/' + form_id, headers)
    getFields(form_fields['form'])

    records = fulcrum.records.search(url_params={'form_id': form_id})
    print streets
    for timed_street in streets:
        found_street['name'] = 'default'
        for row in records['records']:
            update = False
            update_record = row

            try:
                form_street = row['form_values'][fields['street_address']]
                try:
                    form_street = form_street.split(" ")[1]
                except:
                    form_street = ""
            except:
                form_street = ""
            if form_street == timed_street and row['project_id'] == project_id:
               update = True
            if update == True:
                # Check and see if this project has already been created, if not, create it
                new_project['name'] = 'Hour ' + str(count)
                project_search_result = fulcrum.projects.search(url_params={'name': new_project['name']})

                project_found = False
                project_count_num = len(project_search_result['projects'])
                i = 0
                while i < project_count_num:
                    if project_search_result['projects'][i]['name'] == new_project['name']:
                        project_found = True
                        break
                    i += 1
                if project_found == True:
                    update_record['project_id'] = project_search_result['projects'][i]['id']
                else:
                # Create a new project
                    wrapper['project'] = new_project
                    updated_project = fulcrum.projects.create(wrapper)
                    print "updated_project ", "is ", updated_project
                    update_record['project_id'] = updated_project['project']['id']
                #     # Create a new project
                #     wrapper['project'] = new_project
                #     updated_project = fulcrum.projects.create(wrapper)
                #     update_record['project_id'] = updated_project['project_id']
                # else:
                #     update_record['project_id'] = found_street['project_id']
                fulcrum.records.update(row[u'id'], update_record)
        # Increment the count when all residences on this street have been assigned a new project
        count += 1
        print count


def delete_all_projects(form_name, headers, fulcrum):
    form_found = fulcrum.forms.search(url_params={'name': form_name})
    project_name = 'All Residents'
    project_found = fulcrum.projects.search(url_params={'name': project_name})

    form_id = ''
    for form in form_found['forms']:
        if form['name'] == form_name:
            form_id = form['id']

    for project in project_found['projects']:
        print "Deleting Project ", project['name']
        fulcrum.projects.delete(project['id'])










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
    new_project = {}
    wrapper = {}
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
    #
    # for project in project_found['projects']:
    #     print project['name']
    #     print project['id']

    delete_all_projects(form_name, headers, fulcrum)

    new_project['name'] = 'Targeted Residences'
    wrapper['project'] = new_project

    print "Searching for Targeted Project"
    search_output = fulcrum.projects.search(url_params={'name': new_project['name']})
    # Find the Target Project
    project_count = len(search_output['projects'])
    i = 0
    target_found = False
    while i < project_count:
        if search_output['projects'][i]['name'] == new_project['name']:
            print "Project found is ", search_output['projects'][i]
            target_found = True
            updated_project = search_output['projects'][i]
            break
        i += 1
    if target_found == False:
        print "Creating new targeted project"
        updated_project = fulcrum.projects.create(wrapper)
    targeted_project_id = updated_project['project']['id']
    #print updated_project

    # First we need to filter all of the residences into the voters
    # that we care about the most.  This will create a new form that
    # only contains residences where:
    # A resident voted in 2016, 2015, or 2014
    # The residence is not an apartment
    filter_all_residents(form_id, headers, fulcrum, targeted_project_id)

    print "Updated Delaware project"


    street_name_array = create_street_name_array(form_id, headers, fulcrum)
    #print street_name_array
    #street_length_km = find_street_length(form_id, headers, fulcrum, street_name_array[0])
    #print street_length_km
    num_streets = len(street_name_array)
    # while(count < num_streets):
    #     distance_array.append(find_street_length(form_id, headers, fulcrum, street_name_array[count]))
    #     print distance_array[count]
    #     print count
    #     print num_streets
    #     count += 1

    count = 1
    for street in street_name_array:
        street_times.append(find_street_length(form_id, headers, fulcrum, street, targeted_project_id))
        print street, "is", count, "of", num_streets
        count += 1



    print street_times

    # Next sort the street names by distance
    streets_and_times = zip(street_times, street_name_array)
    for street_time in streets_and_times:
        # We only care about streets that can be traversed in less than our allotted time
        if street_time[0] < allotted_time_per_street:
            filtered_street_times.append(street_time)


    print filtered_street_times

    #streets_time_sorted = [x for (y, x) in sorted(zip(street_times, street_name_array))]
    streets_time_sorted = [x for (y, x) in sorted(filtered_street_times, reverse=True)]

    print streets_time_sorted

    #update_to_visit(form_id, headers, fulcrum, streets_time_sorted)


    create_hourly_projects(form_id, headers, fulcrum, streets_time_sorted, targeted_project_id)


    #delete_all_projects(form_name, headers, fulcrum)

   #  print "Updated To Visit Project"
   #
   #  fields = {}
   #  new_project = {}
   #  wrapper = {}
   #  count = 0
   #  num_streets = 10
   #  found_street = {}
   #  found_street['name'] = 'default'
   #  project_found = False
   #
   #
   #  def getFields(data):
   #      if "elements" in data:
   #          for e in data["elements"]:
   #              getFields(e)
   #              fields[e['data_name']] = e['key']
   #
   #
   #  form_fields = GetData('/api/v2/forms/' + form_id, headers)
   #  getFields(form_fields['form'])
   #
   #  #print "Searching for records"
   #  #records = fulcrum.records.search(url_params={'form_id': form_id})
   #  new_project['name'] = 'Test'
   #  print "Creating Test Project"
   #  wrapper['project'] = new_project
   #  print "Wrapper is ", wrapper
   #  #updated_project = fulcrum.projects.create(wrapper)
   #  new_project['name'] = 'Test 2'
   #  print "Creating Test 2 Project"
   #  wrapper['project'] = new_project
   #  print "Wrapper is ", wrapper
   #  #updated_project = fulcrum.projects.create(wrapper)
   # # print "updated_project is ", updated_project
   #  print "Searching for Projects"
   #  search_output = fulcrum.projects.search(url_params={'name': new_project['name']})
   #  print "Correct search output is ", search_output
   #  # print "Searching for wrong project"
   #  # wrong_project = {}
   #  # wrong_project['name'] = 'Wrong'
   #  # wrong_search_output = fulcrum.projects.search(url_params={'name': wrong_project['name']})
   #  # print "Wrong search output is ", wrong_search_output
   #  # possible_output = fulcrum.projects.search(url_params={'projects': new_project})
   #  # print "Different test", possible_output
   #
   #  # Find the Test Project
   #  project_count = len(search_output['projects'])
   #  i = 0
   #  while i < project_count:
   #      if search_output['projects'][i]['name'] == new_project['name']:
   #          print "Project found is ", search_output['projects'][i]
   #      else:
   #          print "Project ", new_project['name'], " not found"
   #      i += 1

    # street_times.append('BELLFIELD')
    # street_times.append('DELAWARE')
    # for timed_street in street_times:
    #     found_street['name'] = 'default'
    #     for row in records['records']:
    #         update = False
    #         update_record = row
    #
    #
    #         update = True
    #         if update == True:
    #             # Check and see if this project has already been created, if not, create it
    #             new_project['name'] = 'Hour ' + str(count)
    #             try:
    #                 found_street = fulcrum.projects.search(url_params={'name': new_project['name']})
    #             except:
    #                 found_street['name'] = 'Does not exist'
    #             print found_street
    #             project_found = False
    #             project_count_num = 0
    #             for project_count in found_street:
    #                 # if found_street[int(project_count)]['name'] == 'Does not exist' or found_street['name'] == 'default':
    #                 if found_street['projects'][project_count_num]['name'] == new_project['name']:
    #                     project_found = True
    #                 project_count_num += 1
    #
    #             if project_found == True:
    #                 #print update_record
    #                 #print found_street
    #                 update_record['project_id'] = found_street['projects'][project_count_num - 1]['id']
    #             else:
    #                 # Create a new project
    #                 wrapper['project'] = new_project
    #                 updated_project = fulcrum.projects.create(wrapper)
    #                 print updated_project
    #                 print update_record
    #                 update_record['project_id'] = updated_project['id']
    #             # # Create a new project
    #             #     wrapper['project'] = new_project
    #             #     updated_project = fulcrum.projects.create(wrapper)
    #             #     update_record['project_id'] = updated_project['project_id']
    #             # else:
    #             #     update_record['project_id'] = found_street['project_id']
    #             fulcrum.records.update(row[u'id'], update_record)
    #     # Increment the count when all residences on this street have been assigned a new project
    #     count += 1
    #     print count




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
