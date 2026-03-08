import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("Warning: PyPDF2 not found. PDF manipulation will be simulated.")

app = Flask(__name__)
app.secret_key = "moudf_secret_key"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    tools = [
        {'name': 'Merge PDF', 'id': 'merge', 'icon': 'merge', 'desc': 'Combine multiple PDFs into one.'},
        {'name': 'Split PDF', 'id': 'split', 'icon': 'content_cut', 'desc': 'Split a PDF into multiple files.'},
        {'name': 'PDF to Word', 'id': 'to-word', 'icon': 'description', 'desc': 'Convert your PDF to DOCX.'},
        {'name': 'Word to PDF', 'id': 'from-word', 'icon': 'picture_as_pdf', 'desc': 'Convert DOCX to PDF.'},
        {'name': 'Compress PDF', 'id': 'compress', 'icon': 'compress', 'desc': 'Reduce PDF file size.'},
        {'name': 'PDF to JPG', 'id': 'to-jpg', 'icon': 'image', 'desc': 'Extract images or save PDF pages as JPG.'}
    ]
    return render_template('index.html', tools=tools)

@app.route('/tool/<tool_id>')
def tool(tool_id):
    tool_names = {
        'merge': 'Merge PDF',
        'split': 'Split PDF',
        'to-word': 'PDF to Word',
        'from-word': 'Word to PDF',
        'compress': 'Compress PDF',
        'to-jpg': 'PDF to JPG'
    }
    name = tool_names.get(tool_id, 'PDF Tool')
    return render_template('tool.html', tool_id=tool_id, tool_name=name)

@app.route('/process/<tool_id>', methods=['POST'])
def process(tool_id):
    if 'files' not in request.files:
        flash('No file part')
        return redirect(url_for('tool', tool_id=tool_id))
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        flash('No selected file')
        return redirect(url_for('tool', tool_id=tool_id))

    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            saved_files.append(filepath)

    if not saved_files:
        flash('Invalid files. Please upload PDF files.')
        return redirect(url_for('tool', tool_id=tool_id))

    output_filename = ""
    try:
        base_name = os.path.splitext(os.path.basename(saved_files[0]))[0]

        if tool_id == 'merge':
            if len(saved_files) < 2:
                flash('Please upload at least 2 PDF files to merge.')
                return redirect(url_for('tool', tool_id=tool_id))
            output_filename = "merged_output.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            merger = PyPDF2.PdfMerger()
            for pdf in saved_files:
                merger.append(pdf)
            merger.write(output_path)
            merger.close()
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'split':
            if not saved_files:
                flash('Please upload a PDF file to split.')
                return redirect(url_for('tool', tool_id=tool_id))
            output_filename = f"{base_name}_split_page_1.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[0])
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'to-word':
            from pdf2docx import Converter
            output_filename = f"{base_name}.docx"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            cv = Converter(saved_files[0])
            cv.convert(output_path, start=0, end=None)
            cv.close()
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'from-word':
            from docx2pdf import convert
            output_filename = f"{base_name}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            convert(saved_files[0], output_path)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'compress':
            output_filename = f"{base_name}_compressed.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'to-jpg':
            from pdf2image import convert_from_path
            images = convert_from_path(saved_files[0], first_page=1, last_page=1)
            output_filename = f"{base_name}_page_1.jpg"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            images[0].save(output_path, 'JPEG')
            return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f'Error processing: {str(e)}')
        return redirect(url_for('tool', tool_id=tool_id))

    flash(f'Successfully processed using {tool_id}!')
    return redirect(url_for('tool', tool_id=tool_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
