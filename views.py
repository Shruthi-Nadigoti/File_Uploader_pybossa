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
from pybossa.cache.helpers import add_custom_contrib_button_to
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
previous_data=[]
CONTAINER="local_upload_directory"
parent_path=current_app.root_path[:current_app.root_path.rfind("/")]
@blueprint.route('/hello')
@login_required
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

def add_task(project):
    project_id=project.id
    project_path=session["zzz"]
    if(session.get("question") is not None):
        for i in ["images","videos","documents","audios"]:
            if len(session["question"][i])!=0:
                project.info["question"][i].extend(session["question"][i])
            print session["question"]
    project_repo.update(project)


    if(session.get("question") is not None):
        for i in ["images","videos","documents","audios"]:
            if os.path.exists(project_path+"/"+i):
                print "in if"
                for file in os.listdir(project_path+"/"+i):
                    p=os.path.join(project_path+"/"+i,file)
                    dictobj={"type":i,"path":p,"subtype":file.rsplit('.',1)[1].lower()}
                    s=json.dumps(dictobj)
                    #print s.type
                    task = Task(project_id=project_id)
                    task.info=dictobj
                    task_repo.save(task)
    session.pop('question', None)

@blueprint.route('/<short_name>/tasks/custom_upload_task',methods=['GET','POST'])
@login_required
def upload_task(short_name):
        (project, owner, n_tasks, n_task_runs,
         overall_progress, last_activity,
         n_results) = project_by_shortname(short_name)
        pro=pro_features()
        project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
        feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
        autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
        project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
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
                        session["zzz"]=zipobj["zzz"]
                        print zipobj["zzz"]
                        #add_task(project.id,zipobj["zzz"])
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

@blueprint.route('/<short_name>/tasks/select_type',methods=['GET', 'POST'])# this url is for the selecting types of folders which user want
@login_required
def select_type(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
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
        print "Going to function"
        p=draft_project(project)
        if(len(previous_data)!=0):
            l=" , ".join(previous_data)
            print l
            flash(l+" questions are already uploaded","info")
        if(p!="-1"):
            return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
        else:
            return redirect_content_type(url_for('.success',short_name=short_name))
    global zipobj
    return  render_template('select_type.html',arr=zipobj,project=project_sanitized,
    pro_features=pro) #sending the classified information to the select_type.html


def store_questions(type_obj,dictobj,project):
    project.info["question"][type_obj].extend(dictobj)
    print project.info["question"][type_obj]
    project_repo.update(project)

def draft_project(project):
    if(session.get("question") is not None):
        print "in draft"
        print session["question"]
    else:
        print "session is None"
    if "question" not in project.info.keys():
        project.info.update({"question":{"images":[],"videos":[],"documents":[],"audios":[]}})
        project_repo.update(project)
    if session.get('question') is None:
        session["question"]={"images":[],"videos":[],"audios":[],"documents":[]}
    for i in list_container:
        if len(project.info["question"][i.lower()])==0 :
            b=list_container.index(i)
            del list_container[b]
            return i.lower()
        else:
            global previous_data
            previous_data.append(i)
    return "-1"


@blueprint.route('/<short_name>/tasks/success', methods=['GET', 'POST'])
@login_required
def success(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    add_task(project)
    global previous_data
    previous_data=[]
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
    return  render_template('success.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html


@blueprint.route('/<short_name>/tasks/images', methods=['GET', 'POST'])
@login_required
def images(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('images.html',project=project_sanitized,
            pro_features=pro)
        session["question"]["images"]=request.form.getlist('question')
        if(request.form.get('submit','')=="submit"):
                p=draft_project(project)
                if(p!="-1"):
                    return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
                else:
                    return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('images.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html



@blueprint.route('/<short_name>/tasks/documents', methods=['GET', 'POST'])
@login_required
def documents(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('documents.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        session["question"]["documents"]=request.form.getlist('question')
        #store_questions("documents",dictobj,project)
        print project.info["question"]
        if(request.form.get('submit','')=="submit"):
            p=draft_project(project)
            if(p!="-1"):
                return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
            else:
                return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('documents.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html




@blueprint.route('/<short_name>/tasks/videos', methods=['GET', 'POST'])
@login_required
def videos(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('videos.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        session["question"]["videos"]=request.form.getlist('question')
        #store_questions("videos",dictobj,project)
        project_repo.update(project)
        if(request.form.get('submit','')=="submit"):
            p=draft_project(project)
            if(p!="-1"):
                return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
            else:
                return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('videos.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html

@blueprint.route('/<short_name>/tasks/audios', methods=['GET', 'POST'])
@login_required
def audios(short_name):
    (project, owner, n_tasks, n_task_runs,
     overall_progress, last_activity,
     n_results) = project_by_shortname(short_name)
    pro=pro_features()
    project_button = add_custom_contrib_button_to(project, get_user_id_or_ip())
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    autoimporter_enabled = feature_handler.autoimporter_enabled_for(current_user)
    project_sanitized, owner_sanitized = sanitize_project_owner(project_button, owner, current_user)
    if request.method == 'POST':
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('audios.html',project=project_sanitized,
            pro_features=pro)
        dictobj={"question":request.form.getlist('question'),"answers":[]}
        print dictobj# here we have to store it in database
        session["question"]["audios"]=request.form.getlist('question')
        #store_questions("audios",dictobj,project)
        if(request.form.get('submit','')=="submit"):
            p=draft_project(project)
            if(p!="-1"):
                return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
            else:
                return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('videos.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html
