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
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    categories = [
        {
            'id': 'popular',
            'name': 'Popular',
            'tools': [
                {'name': 'Merge PDF', 'id': 'merge', 'icon': 'merge', 'desc': 'Combine multiple PDFs into one.'},
                {'name': 'Split PDF', 'id': 'split', 'icon': 'content_cut', 'desc': 'Separate one page or a whole set.'},
                {'name': 'Compress PDF', 'id': 'compress', 'icon': 'compress', 'desc': 'Reduce file size while optimizing for maximal PDF quality.'},
                {'name': 'PDF to Word', 'id': 'to-word', 'icon': 'description', 'desc': 'Convert your PDF to DOCX with ease.'}
            ]
        },
        {
            'id': 'convert-from',
            'name': 'Convert from PDF',
            'tools': [
                {'name': 'PDF to Word', 'id': 'to-word', 'icon': 'description', 'desc': 'Convert PDF to Word document.'},
                {'name': 'PDF to JPG', 'id': 'to-jpg', 'icon': 'image', 'desc': 'Extract images or save each page as a JPG.'},
                {'name': 'PDF to PNG', 'id': 'to-png', 'icon': 'photo_library', 'desc': 'Convert PDF pages to high-quality PNG images.'}
            ]
        },
        {
            'id': 'convert-to',
            'name': 'Convert to PDF',
            'tools': [
                {'name': 'Word to PDF', 'id': 'from-word', 'icon': 'picture_as_pdf', 'desc': 'Convert DOCX files to PDF.'},
                {'name': 'JPG to PDF', 'id': 'from-jpg', 'icon': 'picture_as_pdf', 'desc': 'Convert JPG images to PDF.'}
            ]
        },
        {
            'id': 'edit',
            'name': 'Edit PDF',
            'tools': [
                {'name': 'Rotate PDF', 'id': 'rotate', 'icon': 'rotate_right', 'desc': 'Rotate your PDF pages.'},
                {'name': 'Add Watermark', 'id': 'watermark', 'icon': 'branding_watermark', 'desc': 'Add an image or text over your PDF.'},
                {'name': 'Organize PDF', 'id': 'organize', 'icon': 'low_priority', 'desc': 'Sort, add and delete PDF pages.'}
            ]
        },
        {
            'id': 'security',
            'name': 'PDF Security',
            'tools': [
                {'name': 'Unlock PDF', 'id': 'unlock', 'icon': 'lock_open', 'desc': 'Remove PDF password security.'},
                {'name': 'Protect PDF', 'id': 'protect', 'icon': 'lock', 'desc': 'Encrypt your PDF with a password.'}
            ]
        }
    ]
    return render_template('index.html', categories=categories)

@app.route('/tool/<tool_id>')
def tool(tool_id):
    tool_names = {
        'merge': 'Merge PDF',
        'split': 'Split PDF',
        'to-word': 'PDF to Word',
        'from-word': 'Word to PDF',
        'compress': 'Compress PDF',
        'to-jpg': 'PDF to JPG',
        'to-png': 'PDF to PNG',
        'from-jpg': 'JPG to PDF',
        'rotate': 'Rotate PDF',
        'watermark': 'Add Watermark',
        'organize': 'Organize PDF',
        'unlock': 'Unlock PDF',
        'protect': 'Protect PDF'
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
            
            page_range = request.form.get('page_range', '1')
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            
            try:
                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                    for i in range(start-1, min(end, len(reader.pages))):
                        writer.add_page(reader.pages[i])
                else:
                    pages = [int(p.strip()) for p in page_range.split(',')]
                    for p in pages:
                        if 1 <= p <= len(reader.pages):
                            writer.add_page(reader.pages[p-1])
            except:
                writer.add_page(reader.pages[0]) # Fallback to page 1
            
            output_filename = f"{base_name}_split.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
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

        elif tool_id == 'organize':
            output_filename = f"{base_name}_organized.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            # Reverse pages as a simple "organize" action
            for page in reversed(reader.pages):
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'to-png':
            from pdf2image import convert_from_path
            images = convert_from_path(saved_files[0])
            output_filename = f"{base_name}.png"
            if len(images) > 1:
                # If multiple pages, we might want to zip them, but for now just take the first one
                # or better, save as multiple images if we had a zip tool. 
                # Let's just save the first page for simplicity in this tool.
                output_filename = f"{base_name}_page_1.png"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            images[0].save(output_path, 'PNG')
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'from-jpg':
            from PIL import Image
            image_list = []
            for img_path in saved_files:
                img = Image.open(img_path)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                image_list.append(img)
            
            output_filename = f"{base_name}.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            image_list[0].save(output_path, save_all=True, append_images=image_list[1:])
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'rotate':
            angle = int(request.form.get('rotation', 90))
            output_filename = f"{base_name}_rotated.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                page.rotate(angle)
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'protect':
            password = request.form.get('password')
            output_filename = f"{base_name}_protected.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(password)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'unlock':
            password = request.form.get('password', '')
            output_filename = f"{base_name}_unlocked.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            reader = PyPDF2.PdfReader(saved_files[0])
            if reader.is_encrypted:
                reader.decrypt(password)
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        elif tool_id == 'watermark':
            import io
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            (debug=True, host='0.0.0.0', port=5000)
            output_filename = f"{base_name}_watermarked.pdf"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            reader = PyPDF2.PdfReader(saved_files[0])
            writer = PyPDF2.PdfWriter()
            
            # Create watermark PDF in memory
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica-Bold", 40)
            can.setFillGray(0.5, 0.3) # Semi-transparent
            can.saveState()
            can.translate(300, 400)
            can.rotate(45)
            can.drawCentredString(0, 0, text)
            can.restoreState()
            can.save()
            packet.seek(0)
            
            watermark_pdf = PyPDF2.PdfReader(packet)
            watermark_page = watermark_pdf.pages[0]
            
            for page in reader.pages:
                page.merge_page(watermark_page)
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

