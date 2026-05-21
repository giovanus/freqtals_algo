import os
import shutil

SOURCE_DIR = "codeql_injection_sql"
DEST_DIR = "js_files"

# Répertoires et extensions à exclure
EXCLUDED_DIRS = {"node_modules", "test", "dist", "build"}

os.makedirs(DEST_DIR, exist_ok=True)

count = 0

for root, dirs, files in os.walk(SOURCE_DIR):
    # On modifie dirs en place pour éviter de parcourir les répertoires exclus
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

    for file in files:
        # Extraire uniquement les fichiers .js qui ne sont pas des fichiers minifiés (.min.js)
        if file.endswith(".js") and not file.endswith(".min.js"):
            src = os.path.join(root, file)
            new_name = f"file_{count}.js"
            dst = os.path.join(DEST_DIR, new_name)

            shutil.copy(src, dst)
            count += 1

print("Total JS files extracted:", count)