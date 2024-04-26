
# Editable Flask

Tired of constant client requests to tweak that elusive snippet or image on your **/about** page?

Enter **EditableFlask**. Simply mark sections of your templates with **{% editable %}**, and voilà, they're ready for modification in a sleek admin panel. Say goodbye to the hassle of copy adjustments.

![App Screenshot](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/Image1.png)
## Installation
```bash
  pip install EditableFlask
```
## Usage
```bash
from flask import Flask
from EditableFlask import Edits

app = Flask(__name__)
edits = Edits(app)

```
All edits are neatly saved to disk as JSON. Configure your python file path to store them alongside your app for seamless version control.

```bash
from flask import Flask
from EditableFlask import Edits
import os

app = Flask(__name__)
app.config['FILE_PATH'] = os.path.dirname(__file__)
edits = Edits(app)

@app.route("/")
    def index():
        return render_template('index.html')
```
```html
<!--index.html-->
<!DOCTYPE html>
<html>
<body>
    <!--Add these editable jinja tags to mark them editable-->
<h1>{% editable 'heading' %}My First Heading{% endeditable %}</h1>
<p>{% editable 'paragraph' %}My first paragraph.{% endeditable %}</p>
</body>
</html>

```

## Edits Seaction
Edit any page with registered editable sections directly in the interface. Currently, only static HTML is supported, with Jinja2 support on the roadmap.

![App Screenshot](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/Image2.png)

The **Summernote HTML Editor** is included but not activated by default. Enable it with:
```bash
app.config['EDITS_SUMMERNOTE'] = True
```
* **Uploading Images/Videos**:
    * Summernote enables users to upload images directly into the editor.
    * Users can click on the "Insert Image"/"Insert Video" button, select an image/Video file, and upload it.
    * After uploading, Summernote inserts the image/video into the content, allowing resizing and cropping.
* **Text Formatting**:
    * Summernote offers a wide range of text formatting options.
    * Users can change font style, size, and color, apply bold, italic, or underline styles.
    * Additionally, users can create bulleted or numbered lists and align text as desired.
* **Advanced Features**:
    * Summernote provides advanced text editing features like tables, code blocks, and LaTeX equations.
    * Users can insert tables, format them, and add rows or columns.
    * Furthermore, Summernote supports code blocks with syntax highlighting and LaTeX equations for mathematical expressions.
For Further information Visit [SUMMERNOTE's Webite](https://summernote.org/).

Now you can access all your edits from **/edits** (default) but to make it secure so that no one else could access it is advised to add a security system. There are two ways this can be done:

## Security
**Security Reminder**: EditableFlask doesn't presume your authentication method by default. Protect the admin interface from following methods from developer.
* **Automatic Lock** (Reccomended): In EditableFlask itself there is an **sqlalchamy** based login manager if you want to use that use the following code. There are few points to consider before using the method.
    ```bash
    from flask import Flask, render_template
    from EditableFlask import Edits
    import os

    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here' #DO NOT SHARE THIS WITH ANYONE
    app.config['FILE_PATH'] = os.path.dirname(__file__)
    app.config['SQL_EDITS_LOCKED'] = True
    app.config['EDITS_USERNAME'] = 'your_username'
    app.config['EDITS_PASSWORD'] = 'your_password'
    edits = Edits(app)

    @app.route("/")
    def index():
        return render_template('index.html')
    ```
    ![App Screenshot](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/Image3.png)
    * **EDITS_USERNAME & EDITS_PASSWORD**
        * **Remove EDITS_USERNAME & EDITS_PASSWORD**: After running the app for first time remove EDITS_USERNAME & EDITS_PASSWORD from congif as as soon as the app recives the  EDITS_USERNAME & EDITS_PASSWORD it creates users and keeping USAMENAME and PASSSWORD in your file is not reecomended for deployment purposes.
        * **Using only EDITS_USERNAME or EDITS_PASSWORD**: In the EditableFlask there is a function where if only EDITS_USERNAME or only EDITS_PASSWORD is provided then your username and password will be same.
    * **Few other Terms you could define:**
        * **EDITS_URL**: It is the url where you will be able to access you dashbaord. Here is an example of how you could define it.
        ```bash
        app.config['EDITS_URL'] = '/edits'    #default: '/edits'
        ```
        * **EDITS_ROUTE**: Edits route is where you could login to you editing page. Here is an example of how you could define it.
        ```bash
        app.config['EDITS_ROUTE'] = '/login'    #default: '/login'
        ```
        * **EDITS_STATIC**: This config enables users to get folder view of their static folder even if you have changed the name of static folder it will access it. you could create folder, upload, rename, delete and unzip zipped files.
        ```bash
        app.config['EDITS_STATIC'] = True    #default: False
        ```
        ![App Screenshot](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/Image4.png)
        * **EDITS_PREVIEW**: Preview mode, enabled by default, ensures edits remain hidden until ?preview=true is appended to the URL. Easily toggle preview mode in the admin panel for seamless pre-live editing. Turn on previews for production use.
        ```bash
        app.config['EDITS_PREVIEW'] = False    #default: True
        ```
        ![App Screenshot](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/Image5.png)
        * **PERMANENT_SESSION_LIFETIME**: If session.permanent is true, the cookie’s expiration will be set this number of seconds in the future. Can either be a datetime.timedelta or an int. Flask’s default cookie implementation validates that the cryptographic signature is not older than this value.
        ```bash
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)   #default: 60min
        ```
        * **SQLALCHEMY_DATABASE_URI**: The database connection URI used for the default engine. It can be either a string or a SQLAlchemy URL instance. See below for example.
        ```bash
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' #default: sqlite:///users.db
        ```
         * **SQLALCHEMY_TRACK_MODIFICATIONS**: If enabled, all insert, update, and delete operations on models are recorded, then sent in models_committed and before_models_committed signals when session.commit() is called.This adds a significant amount of overhead to every session. Prefer using SQLAlchemy’s ORM Events directly for the exact information you need.
        ```bash
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #default: False
        ```
* **Manual Lock**: If you alredy have a user-managemnt system and want to add same to it then, we also have support that users too. Here is an example of cose of how you code should look like.
    ```bash
    from flask import Flask
    from EditableFlask import Edits
    import os

    app = Flask(__name__)
    app.config['FILE_PATH'] = os.path.dirname(__file__)
    app.config['EDITS_LOCKED'] = True
    app.config['EDITS_ROUTE'] = '/login'
    #Mention your apps login route where you are loggin in users.
    edits = Edits(app)
    ```
## Resources
 - [MDI Icons From pictogrammers](https://pictogrammers.github.io/@mdi/font/2.0.46/)

## Authors
- [@MahirShah07](https://www.mahirshah.dev)

View This Repository at GitHub: https://github.com/MahirShah07/EditableFlask
## Support
For support, email mahir.shah.sd@gmail.com or join our contact me from my Website https://mahirshah.dev.


![Logo](https://raw.githubusercontent.com/MahirShah07/EditableFlask/main/readme-images/logo.png)
## Copyright 2024 Mahir Shah
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


