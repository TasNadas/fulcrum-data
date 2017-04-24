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


def recordupdate(form_id, headers, fulcrum):
    # fields = {}
    # def getFields(data):
    #     if "elements" in data:
    #         for e in data["elements"]:
    #             getFields(e)
    #             fields[e['key']] = e['data_name']
    #
    # form_fields = GetData('/api/v2/forms/' + form_id, headers)
    # getFields(form_fields['form'])
    #
    # recordAPIurl = '/api/v2/records?form_id=%s' % (form_id)
    #
    # print fields
    #
    # for page in range(getRecordPageCount(recordAPIurl, headers)):
    #     record_data = GetData(recordAPIurl + '&page=%i' % (page + 1), headers)
    #
    #     print 'here'
    #
    #     records = record_data['records']
    #     for row in records:
    #         updatedrow = row
    #         updatedrow['form_values']['3f1c'] = 'I AM AWESOME'
    #         fulcrum.records.update(row['id'], updatedrow)

    tbl = []
    records = fulcrum.records.search(url_params={'form_id': form_id})
    for row in records['records']:
        # print row
        tbl.append([row['form_values']['12ac'], row['id']])

    return tbl

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

    formname = 'CH Voters 2017'
    # formname = 'test'

    set = GetData('/api/v2/forms', headers)

    form_id = ''
    for form in set['forms']:
        print form['name']
        print form['id']
        if form['name'] == formname:
            form_id = form['id']

    # print form_id

    # tbl = recordupdate(form_id, headers, fulcrum)
    # exporttocsv(tbl)