import zipfile,tarfile,os,shutil,time #used create,delete the folder
def extract_files_local(fullpath,filename,project_id): #to extract the files fullpath is the parent directory and filename to is name of the file

    #print "%s"%fullpath
    #print "%s"%filename
    print project_id
    name=filename.rsplit('.',1)[0].lower()+"1"
    #name = "%s_%i" % (name,time.time()) #this shoud be replaced with project name(unic)
    name="%s_%i"%(project_id,time.time())
    actual_name=""
    x=[]
    if  filename.rsplit('.', 1)[1].lower()=="zip": # checking extension with zip
    	 zfile = zipfile.ZipFile(fullpath+"/"+filename) #opening the file
         zfile.extractall(fullpath+"/") #extraction of zip
         actual_name=filename[:filename.rfind("zip")-1] #getting the extracted folder name
         x=zfile.namelist() #list of files the zip file
    elif "tar.gz" in filename and filename.rsplit('.', 1)[1].lower()=="gz":#checking the extension with tar.gz
         tar = tarfile.open(fullpath+"/"+filename,'r:gz')#opening the file
         tar.extractall(fullpath+"/") #extracting
         actual_name=filename[:filename.rfind("tar.gz")-1] #getting the name of the extracted file
         x=tar.getnames() #getting the list of files in tar.gz

    os.makedirs(fullpath+"/"+name+"/images") #creating subfolders
    os.makedirs(fullpath+"/"+name+"/videos")
    os.makedirs(fullpath+"/"+name+"/audios")
    os.makedirs(fullpath+"/"+name+"/documents")

    for f in x: #looping through the files to classify
         srcfullpath = fullpath+ "/" + f
         #print srcfullpath
         if('.' in f):
                m=time.time()
                f_name=srcfullpath[srcfullpath.rfind('/')+1:] #getting only filename
                #f_name_only=f_name[:f_name.rfind('.')]
                if(f.rsplit('.',1)[1].lower() in ['png','gif','jpeg','jpg']):#checking with file extension
                    dst =fullpath+"/"+name+"/images"#defining the destination folder
                    shutil.move(srcfullpath, dst)#moving the file to destination
                    os.rename(dst+"/"+f_name,(dst+"/"+str(m)+f_name))#renaming the files by adding some  prifix integer to the filename
                elif(f.rsplit('.',1)[1].lower() in ['pdf','doc','txt','odt','docx']):#checking the extension with document related things
                    dst =fullpath+"/"+name+"/documents"
                    shutil.move(srcfullpath, dst)
                    os.rename(dst+"/"+f_name,(dst+"/"+str(m)+f_name))
                elif(f.rsplit('.',1)[1].lower() in ['mp4','mkv']):#checking the extension with videos related things
                    dst =fullpath+"/"+name+"/videos"
                    shutil.move(srcfullpath, dst)
                    os.rename(dst+"/"+f_name,(dst+"/"+str(m)+f_name))
                elif(f.rsplit('.',1)[1].lower() in ['mp3']):#checking the extension with audio related things
                    dst =fullpath+"/"+name+"/audio"
                    shutil.move(srcfullpath, dst)
                    os.rename(dst+"/"+f_name,(dst+"/"+str(m)+f_name))

    dictcount={} #creating empty dictionary to store the number of files related to the classified folder

    dirListing = os.listdir(fullpath+"/"+name+"/images")#counting list in images
    if(len(dirListing)!=0): #number of files are zero then we won't store it
        dictcount.update({'Images':len(dirListing)})#adding information to the dictionary
    dirListing = os.listdir(fullpath+"/"+name+"/videos")
    if(len(dirListing)!=0):
        dictcount.update({'Videos':len(dirListing)})
    dirListing = os.listdir(fullpath+"/"+name+"/documents")
    if(len(dirListing)!=0):
        dictcount.update({'Documents':len(dirListing)})
    dirListing = os.listdir(fullpath+"/"+name+"/audios")
    if(len(dirListing)!=0):
        dictcount.update({'Audio':len(dirListing)})
    dictcount.update({'zzz':fullpath+"/"+name})#storing the classified folder path in dictionary
    #print fullpath+"/"+actual_name
    if os.path.exists(fullpath+"/"+actual_name):
        shutil.rmtree(fullpath+"/"+actual_name)#deleting the actual folder
    if os.path.exists(fullpath+"/"+filename):
        #print "inner"
        p=fullpath+"/"+filename
        #print p
        os.remove(p)#deleting the zip or tar.gz file
    if(len(dictcount)<2):
        if os.path.exists(fullpath+"/"+name):
            shutil.rmtree(fullpath+"/"+name)#removing the classified folder if there are no files
    return dictcount #sending the data to called function"""
