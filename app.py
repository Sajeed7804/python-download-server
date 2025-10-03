import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, session, flash
import ssl

app = Flask(__name__)
app.secret_key = "supersecret"

FILE_DIR = "files"
USERNAME = "admin"
PASSWORD = "password"

# ---- Auth Routes ----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = USERNAME
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---- Main Routes ----
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    files = os.listdir(FILE_DIR)
    return render_template("index.html", files=files)

@app.route("/download/<filename>")
def download(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    return send_from_directory(FILE_DIR, filename, as_attachment=True)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        f = request.files.get("file")
        if not f or f.filename == "":
            flash("No file selected", "warning")
            return redirect(request.url)
        f.save(os.path.join(FILE_DIR, str(f.filename)))
        flash(f"Uploaded {f.filename}", "success")
        return redirect(url_for("index"))
    return render_template("upload.html")

# ---- Run App with SSL ----
if __name__ == "__main__":
    # auto-generate self-signed certificate if not exists
    cert_file = "cert.pem"
    key_file = "key.pem"
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("Generating self-signed certificate...")
        from OpenSSL import crypto
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        cert = crypto.X509()
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, "sha256")
        with open(cert_file, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(key_file, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    # run Flask app with HTTPS
    context = (cert_file, key_file)
    app.run(host="0.0.0.0", port=5000, ssl_context=context, debug=True)
