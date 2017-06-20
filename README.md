# File Importer In Pybossa
This is Pybossa plugin to import the files from the local machine.
## How to Import the files
- ### Upload File
     - It accepts only zip and tar.gz extension files.In this we can put images,documents,videos,audios related files.We can have subfolders also.
- ### Add Question
     - We should write the questions for files which we have uploaded.That's it you can see "successfully uploaded " message on your screen

Note:If the questions are already uploaded for particular class of file then it won't ask to write question for corresponding class

## Installation
- Clone this repository paste it in pybossa/pybossa/plugins directory.
- Make the following changes 
   -Create frg.html file in pybossa/themes/default/templates/projects/tasks directory.
   -Write the following code in it
   
``` {% from "projects/_helpers.html" import render_project_card_option %}
{{ render_project_card_option(project, upload_method, title=_('Fundamental Research Group'), explanation=_('Use files from local machine'), link=url_for("file_test.upload_task", short_name=project.short_name, type='frg'), link_action_text=_('Import data'), icon='upload')}} ```

  - In pybossa/importers/importer.py file make some changes as below code
    ```
     def __init__(self):
        """Init method."""
        self._importers = dict(csv=BulkTaskCSVImport,
                               gdocs=BulkTaskGDImport,
                               epicollect=BulkTaskEpiCollectPlusImport,
                               s3=BulkTaskS3Import,
                               frg="",
                               )
        self._importer_constructor_params = dict()```
        
        
Now restart the server.Now you can see Fundamental Research Importer(File Uploader) in Importer options


