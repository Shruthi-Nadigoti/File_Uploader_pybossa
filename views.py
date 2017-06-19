#from pybossa.view.projects import blueprint
from flask import Blueprint,request,Response,render_template,redirect,flash,current_app,url_for,session
import time
from flask.ext.babel import gettext
from .forms import *
from pybossa.util import (Pagination, admin_required, get_user_id_or_ip, rank,
                          handle_content_type, redirect_content_type,
                          get_avatar_url)
from flask.ext.login import login_required, current_user
from pybossa.core import uploader
from file_extraction import extract_files_local
from flask import send_from_directory
import os,shutil
from pybossa.core import db

from pybossa.view.projects import sanitize_project_owner,project_by_shortname,pro_features

from pybossa.model.task import Task
import json
from pybossa.core import task_repo,project_repo
from pybossa.pro_features import ProFeatureHandler
from pybossa.model.project import Project
from pybossa.cache import projects as cached_projects
from sqlalchemy import update

blueprint = Blueprint('file_test', __name__,template_folder='templates',static_folder="static")
zipobj={}
list_container=[]
CONTAINER="local_upload_directory"
parent_path=current_app.root_path[:current_app.root_path.rfind("/")]
@blueprint.route('/hello')
def hello():
    return redirect(url_for("file_test.select_type"))

def allowed_file(filename):
    """Return True if valid, otherwise false."""
    if '.' in filename:
        if filename.rsplit('.', 1)[1].lower()=="zip" :
            return True
        elif "tar.gz" in filename and filename.rsplit('.', 1)[1].lower()=="gz" :
            return True
    flash('Only zip and tar.gz extensions are allowed','danger')
    return False


def check_file_size(file_path):
    size=os.path.getsize(file_path)
    if(size<=1024*1024*5):
        return True
    print size
    return False

def add_task(project_id,project_path):

    for i in ["images","videos","documents","audios"]:
        if os.path.exists(project_path+"/"+i):
            print "in if"
            for file in os.listdir(project_path+"/"+i):
                p=os.path.join(project_path+"/"+i,file)
                dictobj={"type":i,"path":p,"subtype":file.rsplit('.',1)[1].lower()}
                s=json.dumps(dictobj)
                #print s.type
                #task = Task(project_id=project_id)
                #task.info=dictobj
                #task_repo.save(task)


@blueprint.route('/<short_name>/tasks/custom_upload_task',methods=['GET','POST'])
def upload_task(short_name):
    try:
        (project, owner, n_tasks, n_task_runs,
         overall_progress, last_activity,
         n_results) = project_by_shortname(short_name)
        pro=pro_features()
        project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
        if request.method=='POST':
            upload_form=TaskUpload()
            if upload_form.validate_on_submit():
                _file=request.files['avatar']
                #extract_files_local(parent_path+"/uploads"+CONTAINER,_file.filename)
                if _file and allowed_file(_file.filename):
                    _file.save(os.path.join((parent_path+'/uploads/'+CONTAINER) , _file.filename))
                    if(check_file_size(parent_path+'/uploads/'+CONTAINER+"/"+_file.filename)):

                        global zipobj
                        zipobj=extract_files_local((parent_path+"/uploads/"+CONTAINER),_file.filename,project.id)
                        print zipobj["zzz"]
                        add_task(project.id,zipobj["zzz"])
                        return redirect_content_type(url_for('.select_type',
                                                             short_name=short_name))
                    else:
                        if os.path.exists(parent_path+'/uploads/'+CONTAINER+"/"+_file.filename):
                            os.remove(parent_path+'/uploads/'+CONTAINER+"/"+_file.filename)
                        flash('File Size should be less than 5 MB');
            else:
                flash(gettext('Please upload the file'),'warning')

        upload_form =TaskUpload()
        response =dict(template='/upload_form.html',
                       upload_form=upload_form,
                       project=project_sanitized,
                       pro_features=pro
                       )
        return handle_content_type(response)
    except Exception:
        return False

@blueprint.route('/<short_name>/tasks/select_type',methods=['GET', 'POST'])# this url is for the selecting types of folders which user want
def select_type(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
    print short_name
    li=["Images","Videos",'Audios','Documents'] #classification files
    if request.method == 'POST':
        global list_container
        list_container=request.form.getlist('selecttype') #selected classification list
        for i in li:
            if i not in list_container:
                n=request.form.getlist('filepath')[0]#this is parent path of the folder which were unchecked by user
                if os.path.exists(n+"/"+i.lower()):
                    shutil.rmtree(n+"/"+i.lower()) #deletion of folder
        for i in list_container:
            b=list_container.index(i)
            del list_container[b]
            print i.lower()
            return redirect_content_type(url_for('.'+i.lower(),short_name=short_name))
    global zipobj
    #for i in li:
    #    if(i not in zipobj.keys()):
    #        flash('You do not have any '+i,'info') #giving information about the folders which user don't have
    return  render_template('select_type.html',arr=zipobj,project=project_sanitized,
    pro_features=pro) #sending the classified information to the select_type.html



@blueprint.route('/<short_name>/tasks/documents', methods=['GET', 'POST'])
def documents(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('documents.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        store_questions("documents",dictobj,project)
        print project.info["question"]
        if(request.form.get('submit','')=="submit"):
            global list_container
            print len(list_container)
            if(len(list_container)<1):
                return "success"
            else:
                for i in list_container:
                    b=list_container.index(i)
                    del list_container[b]
                    print i.lower()
                    return redirect_content_type(url_for('.'+i.lower(),short_name=short_name))
    return  render_template('documents.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html


def store_questions(type_obj,dictobj,project):
    if "question" not in project.info.keys():
        project.info.update({"question":{"images":[],"videos":[],"documents":[],"audios":[]}})
        db.session.commit()

    project.info["question"][type_obj].append(dictobj)
    print project.info["question"][type_obj]
    project_repo.update(project)

@blueprint.route('/<short_name>/tasks/images', methods=['GET', 'POST'])
def images(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Please enter the question","warning")
            return  render_template('images.html',project=project_sanitized,
            pro_features=pro)
        if(request.form.getlist('answer')[0]=="" or request.form.getlist('answer')[1]==""):
            flash("Atleast 2 answers are required","warning")
            return  render_template('images.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.get('question'),"answers":request.form.getlist('answer')}
        print dictobj# here we have to store it in database
        #pj = Project.query.filter_by(short_name=short_name).first()
        store_questions("images",dictobj,project)
        #project = Project.query.filter_by(short_name=short_name).first()
        print project.info.keys()
        print project.info["question"]

        if(request.form.get('submit','')=="submit"):
            global list_container
            print len(list_container)
            if(len(list_container)<1):
                return "success"
            else:
                for i in list_container:
                    b=list_container.index(i)
                    del list_container[b]
                    return redirect_content_type(url_for('.'+i.lower(),short_name=short_name))
    return  render_template('images.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html


@blueprint.route('/<short_name>/tasks/videos', methods=['GET', 'POST'])
def videos(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('videos.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        store_questions("videos",dictobj,project)
        project_repo.update(project)
        if(request.form.get('submit','')=="submit"):
            global list_container
            print len(list_container)
            if(len(list_container)<1):
                return "success"
            else:
                for i in list_container:
                    b=list_container.index(i)
                    del list_container[b]
                    print i.lower()
                    return redirect_content_type(url_for('.'+i.lower(),short_name=short_name))
    return  render_template('videos.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html

@blueprint.route('/<short_name>/tasks/audios', methods=['GET', 'POST'])
def audios(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('audios.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        store_questions("audios",dictobj,project)
        if(request.form.get('submit','')=="submit"):
            global list_container
            print len(list_container)
            if(len(list_container)<1):
                return "success"
            else:
                for i in list_container:
                    b=list_container.index(i)
                    del list_container[b]
                    print i.lower()
                    return redirect_content_type(url_for('.'+i.lower(),short_name=short_name))
    return  render_template('videos.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html
