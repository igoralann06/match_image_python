from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import shutil

app = Flask(__name__)

# Configure paths
PRODUCTS_DIR = "products"
TARGET_DIR = "target"
ITEMS_PER_PAGE = 20

# Ensure target directory exists
os.makedirs(TARGET_DIR, exist_ok=True)

def get_image_list():
    """Recursively get all image file paths from the products directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = []
    for root, _, files in os.walk(PRODUCTS_DIR):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                rel_path = os.path.relpath(os.path.join(root, file), PRODUCTS_DIR)
                image_files.append(rel_path)
    return image_files

@app.route('/products/<path:filename>')
def serve_products(filename):
    return send_from_directory('products', filename)

@app.route('/')
def index():
    """Display images with pagination."""
    images = get_image_list()
    page = int(request.args.get('page', 1))
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    total_pages = -(-len(images) // ITEMS_PER_PAGE)  # Ceiling division

    return render_template("index.html", images=images[start:end], page=page, total_pages=total_pages)

@app.route('/submit', methods=['POST'])
def submit():
    """Handle image selection and copy to target directory."""
    selected_images = request.form.getlist('selected_images')
    page = request.form.get('page', 1)  # Preserve the page number

    for img in selected_images:
        src_path = os.path.join(PRODUCTS_DIR, img)
        dest_path = os.path.join(TARGET_DIR, os.path.basename(img))
        shutil.copy(src_path, dest_path)

    return redirect(url_for('index', page=page))

if __name__ == '__main__':
    app.run()
