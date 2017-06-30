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
from pybossa.core import user_repo
from pybossa.model.user import User
from pybossa.plugins.quiz.views import is_quiz_provided


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
    """size=os.path.getsize(file_path)
    if(size<=1024*1024*5):
        return True
    print size
    return False"""
    return True
def store_questions(project):

    if(session.get("question") is not None):
        for i in ["images","videos","documents","audios"]:
            if len(session["question"][i])!=0:
                project.info["questionSet"][i]=session["question"][i]
            print session["question"]
    project_repo.update(project)

def add_task(project):
    store_questions(project)
    project_id=project.id
    project_path=session["zzz"]
    if(session.get("question") is not None):
        for i in ["images","videos","documents","audios"]:
            if os.path.exists(project_path+"/"+i):
                print "in if"
                for file in os.listdir(project_path+"/"+i):
                    p=os.path.join(project_path+"/"+i,file)
                    p=p[p.rfind("uploads"):]
                    print p
                    dictobj={"type":i,"url":"/"+p,"subtype":file.rsplit('.',1)[1].lower()}
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
                        zipobj.pop("zzz",None)
                        if "directory_names" not in project.info.keys():
                            project.info.update({"directory_names":[]})
                        project.info["directory_names"].append(session["zzz"])
                        project_repo.update(project)
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
    global zipobj
    li=["Images","Videos",'Audios','Documents'] #classification files
    if request.method == 'POST':
        global list_container
        list_container=request.form.getlist('selecttype') #selected classification list
        for i in li:
            if i not in list_container:
                n=session["zzz"]#this is parent path of the folder which were unchecked by user
                if os.path.exists(n+"/"+i.lower()):
                    shutil.rmtree(n+"/"+i.lower()) #deletion of folder
        if(len(list_container)==0):
            flash("You must select atleast one file","danger")
            return  render_template('select_type.html',arr=zipobj,project=project_sanitized,pro_features=pro)
        print "Going to function"
        global previous_data
        p=draft_project(project)
        if(len(previous_data)!=0):
            l=" , ".join(previous_data)
            print l
            flash(l+" questions are already uploaded","info")
        if(p!="-1"):
            return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
        else:
            return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('select_type.html',arr=zipobj,project=project_sanitized,
    pro_features=pro) #sending the classified information to the select_type.html




def draft_project(project):
    if(session.get("question") is not None):
        print "in draft"
        print session["question"]
    else:
        print "session is None"

    if "questionSet" not in project.info.keys():
        project.info.update({"questionSet":{"images":[],"videos":[],"documents":[],"audios":[]}})
        project_repo.update(project)
    if "importer_type" not in project.info.keys():
        project.info.update({"importer_type":"frg"})
        project_repo.update(project)
    if session.get('question') is None:
        session["question"]={"images":[],"videos":[],"audios":[],"documents":[]}
    for i in list_container:
        if len(project.info["questionSet"][i.lower()])==0 :
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
    flash("Your Tasks Uploded Successfully","success")
    #return  render_template('success.html',project=project_sanitized,pro_features=pro) #we are going to tags.html
    if(not is_quiz_provided(project.id)):
        return redirect(url_for('quiz.create_quiz',short_name=short_name))
    else:
        return redirect(url_for('project.details',short_name=short_name))
    #return  render_template('success.html',project=project_sanitized,pro_features=pro) #we are going to tags.html




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
    if(session.get("question") is None):
        return redirect_content_type(url_for('.success',short_name=short_name))
    if request.method == 'POST':
        type_q="normal"
        answer=[]
        if(request.form.get('question','')==""):
            flash("Atleast 1 question is required","warning")
            return  render_template('images.html',project=project_sanitized,
            pro_features=pro)
        if(request.form.get('checkbox','')!=""):
            if(request.form.getlist('answer')[0]=="" or request.form.getlist('answer')[1]==""):
                flash("Atleast 2 answers are required","warning")
                return  render_template('images.html',project=project_sanitized,
                pro_features=pro)
            else:
                type_q="mcqs"
                answer=request.form.getlist('answer')
        dictobj={"questionString":request.form.get('question'),"answers":answer,"type":type_q}
        session["question"]["images"].append(dictobj)
        if(request.form.get('submit','')=="submit"):
                p=draft_project(project)
                if(p!="-1"):
                    return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
                else:
                    return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('images.html',project=project_sanitized,pro_features=pro) #we are going to tags.html



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
    if(session.get("question") is None):
        return redirect_content_type(url_for('.success',short_name=short_name))
    if request.method == 'POST':
        type_q="normal"
        answer=[]
        if(request.form.get('question','')==""):
            flash("Please enter the question","warning")
            return  render_template('documents.html',project=project_sanitized,
            pro_features=pro)
        if(request.form.get('checkbox','')!=""):
            if(request.form.getlist('answer')[0]=="" or request.form.getlist('answer')[1]==""):
                flash("Atleast 2 answers are required","warning")
                return  render_template('documents.html',project=project_sanitized,
                pro_features=pro)
            else:
                type_q="mcqs"
                answer=request.form.getlist('answer')
        dictobj={"questionString":request.form.get('question'),"answers":answer,"type":type_q}
        session["question"]["documents"].append(dictobj)
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
    if(session.get("question") is None):
        return redirect_content_type(url_for('.success',short_name=short_name))
    if request.method == 'POST':
        type_q="normal"
        answer=[]
        if(request.form.get('question','')==""):
            flash("Please enter the question","warning")
            return  render_template('videos.html',project=project_sanitized,
            pro_features=pro)
        if(request.form.get('checkbox','')!=""):
            if(request.form.getlist('answer')[0]=="" or request.form.getlist('answer')[1]==""):
                flash("Atleast 2 answers are required","warning")
                return  render_template('videos.html',project=project_sanitized,
                pro_features=pro)
            else:
                type_q="mcqs"
                answer=request.form.getlist('answer')
        dictobj={"questionString":request.form.get('question'),"answers":answer,"type":type_q}
        session["question"]["videos"].append(dictobj)
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
    if(session.get("question") is None):
        return redirect_content_type(url_for('.success',short_name=short_name))
    if request.method == 'POST':
        type_q="normal"
        answer=[]
        if(request.form.get('question','')==""):
            flash("Please enter the question","warning")
            return  render_template('audios.html',project=project_sanitized,
            pro_features=pro)
        if(request.form.get('checkbox','')!=""):
            if(request.form.getlist('answer')[0]=="" or request.form.getlist('answer')[1]==""):
                flash("Atleast 2 answers are required","warning")
                return  render_template('audios.html',project=project_sanitized,
                pro_features=pro)
            else:
                type_q="mcqs"
                answer=request.form.getlist('answer')
        dictobj={"questionString":request.form.get('question'),"answers":answer,"type":type_q}
        session["question"]["audios"].append(dictobj)
        if(request.form.get('submit','')=="submit"):
                p=draft_project(project)
                if(p!="-1"):
                    return redirect_content_type(url_for('.'+p.lower(),short_name=short_name))
                else:
                    return redirect_content_type(url_for('.success',short_name=short_name))
    return  render_template('audios.html',project=project_sanitized,
    pro_features=pro) #we are going to tags.html
