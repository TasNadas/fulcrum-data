import fulcrum, sys, json, os, codecs
import httplib2 as http
from fulcrum import Fulcrum

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

uname = "tas@nadas.org"
pw    = "Nadas4CH!"

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


def getRecordPageCount(url, headers):
    return GetData(url + '&page=0', headers)['total_pages']


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
                y2013 = i['form_values'][fields['g201311']]
            except:
                y2013 = ""
            try:
                birth = i['form_values'][fields['birth_year']]
            except:
                birth = ""
            if party == "DEM" and (y2015 == "Y" or y2014 == "Y" or y2013 == "Y") and int(birth) > 1970:
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
            if numvoters > 0:
                update = True

        if update == True:
            update_record['form_values'][fields['comments']] = 'updated'
            update_record['project_id'] = '86d4b7cd-4e8d-4260-b69c-747301c06835'
            fulcrum.records.update(row[u'id'], update_record)


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

    api_key = os.environ['FULCRUM_API_KEY']*

    fulcrum = Fulcrum(key=api_key)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
        'X-ApiToken': api_key
    }

    formname = 'CH Voters 2017'
    # formname = 'test'

    set = GetData('/api/v2/forms', headers)

    form_id = ''
    for form in set['forms']:
        # print form['name']
        # print form['id']
        if form['name'] == formname:
            form_id = form['id']

    # print form_ida

    # recordupdate(form_id, headers, fulcrum)
    resetrecordstooneproject(form_id, headers, fulcrum)
    # exporttocsv(tbl)