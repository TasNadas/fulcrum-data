import sys, os, codecs, csv

parentfile = r'C:\data\temp\Children\ch_voters_2017.csv'
childfile = r'C:\data\temp\Children\children2.csv'
pfilename = "parent"
cfilename = "child"
outdirectory = r'C:\data\temp\Children2'


def csvread(filename):
    open_csv = file(filename)
    csvtbl = csv.DictReader(open_csv)

    arry = []
    for row in csvtbl:
        arry.append(row)

    return arry


def pcjoin(parent, child):
    maxrows = 9800
    i = 0
    parentarry = []
    childrenarry = []
    for prow in parent:
        if i > maxrows:
            exporttocsv(parentarry, outdirectory, pfilename)
            exporttocsv(childrenarry, outdirectory, cfilename)
            parentarry = []
            childrenarry = []
            i = 0
        else:
            childarry = []
            for crow in child:
                # print crow
                if prow["fulcrum_id"] == crow["fulcrum_parent_id"]:
                    # print crow
                    childarry.append(crow)
                    i += 1
            for childrow in childarry:
                childrenarry.append(childrow)
        parentarry.append(prow)

    exporttocsv(parentarry, outdirectory, pfilename)
    exporttocsv(childrenarry, outdirectory, cfilename)


def exporttocsv(tbl, outdir, outname):
    filenum = 1
    while os.path.exists(os.path.join(outdir, outname + str(filenum) + ".csv")):
        filenum += 1

    fname = os.path.join(outdir, outname + str(filenum) + ".csv")

    csvfile = codecs.open(fname, 'w', 'utf-8')

    headerarry = []
    firstarry = []
    firstrow = True
    for row in tbl:
        for header in row:
            if firstrow:
                headerarry.append(header)
                firstarry.append(row[header])
            else:
                csvfile.write(row[header] + ",")
        if firstrow:
            for header in headerarry:
                csvfile.write(header + ",")
                firstrow = False
            csvfile.write("blank\n")
            for frow in firstarry:
                csvfile.write(frow + ",")
        csvfile.write("\n")
    # csvfile.write("\"Tributary Area\",\"Diameter (in)\",\"Length (ft)\",\"Pipe Size X Length (in x ft)")
    # csvfile.write("\"\n")
    #
    # for row in tbl:
    #     csvfile.write("\"" + row[0] + "\",\"" + str(row[1]) + "\",\"" + str(row[2]) + "\",\"" + str(row[3]))
    #     csvfile.write("\"\n")

    # csvfile.write("\"\n")

    csvfile.close()


if __name__ == '__main__':
    parent = csvread(parentfile)
    child = csvread(childfile)

    # print child

    pcjoin(parent, child)


    print("DONE!")