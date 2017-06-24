# File Importer for Pybossa
This is Pybossa plugin to import the files from the local machine.

## Installation
- Clone this repository and rename it to file_uploader and paste it in pybossa/pybossa/plugins directory.
- Make the following changes 
   - Create frg.html file in pybossa/themes/default/templates/projects/tasks directory.
   - Write the following code in it
   
``` 
{% from "projects/_helpers.html" import render_project_card_option %}
{{ render_project_card_option(project, upload_method, title=_('Fundamental Research Group'), 
explanation=_('Use files from local machine'), link=url_for("file_test.upload_task",
short_name=project.short_name, type='frg'), link_action_text=_('Import data'), icon='upload')}} 

```

  - In pybossa/importers/importer.py file make some changes to the constructor as below code
  
    ```
     def __init__(self):
        """Init method."""
        self._importers = dict(csv=BulkTaskCSVImport,
                               gdocs=BulkTaskGDImport,
                               epicollect=BulkTaskEpiCollectPlusImport,
                               s3=BulkTaskS3Import,
                               frg="",
                               )
        self._importer_constructor_params = dict()
        
       ```
   - Replace the code of delete(short_name) method in  pybossa/view/project.py file
   ```
   @blueprint.route('/<short_name>/delete', methods=['GET', 'POST'])
   @login_required
   def delete(short_name):
       (project, owner, n_tasks,
       n_task_runs, overall_progress, last_activity,
       n_results) = project_by_shortname(short_name)
       title = project_title(project, "Delete")
       ensure_authorized_to('read', project)
       ensure_authorized_to('delete', project)
       pro = pro_features()
       project_sanitized, owner_sanitized = sanitize_project_owner(project, owner, current_user)
       if request.method == 'GET':
           response = dict(template='/projects/delete.html',
                           title=title,
                           project=project_sanitized,
                           owner=owner_sanitized,
                           n_tasks=n_tasks,
                           overall_progress=overall_progress,
                           last_activity=last_activity,
                           pro_features=pro,
                           csrf=generate_csrf())
           return handle_content_type(response)
       if("directory_names" in project.info.keys()):
           for i in project.info["directory_names"]:
               if os.path.exists(i):
                   shutil.rmtree(i)#deleting the actual folder
       project_repo.delete(project)
       auditlogger.add_log_entry(project, None, current_user)
       flash(gettext('Project deleted!'), 'success')
       return redirect_content_type(url_for('account.profile', name=current_user.name))
   ```
        
        
Now restart the server.You can see Fundamental Research Importer(File Uploader) in Importer options

## How to Import the files
- ### Upload File
     - Go to importers and choose the fundamental Research importer
     - Upload the file (it accepts only zip and tar.gz extension files.In this we can put images,documents,videos,audios related files.We can have subfolders also)
- ### Add Question
     - We should write the questions for files which we have uploaded.That's it you can see "successfully uploaded " message on your screen

> Note:If the questions are already uploaded for particular class of file then it won't ask to write question for corresponding class

