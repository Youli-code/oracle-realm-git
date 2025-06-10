import os
import shutil
import tempfile
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
LIBRARY_BASE_PATH = "libraries"


class GitImportRequest(BaseModel):
    repo_url: str
    realm: str


@router.post("/api/import-github")
def import_github_repo(data: GitImportRequest):
    repo_url = data.repo_url.strip()
    realm = data.realm.strip().lower()
    temp_dir = tempfile.mkdtemp()

    try:
        # Clone the GitHub repo
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)

        # Source folders
        kbd_src = os.path.join(temp_dir, "kbd")
        tsd_src = os.path.join(temp_dir, "tsd")

        if not os.path.isdir(kbd_src) or not os.path.isdir(tsd_src):
            raise HTTPException(
                status_code=400,
                detail="Repo must contain 'kbd/' and 'tsd/' folders with .json files.",
            )

        # Destination paths
        kbd_dest = os.path.join(LIBRARY_BASE_PATH, realm, "documents", "kbd")
        tsd_dest = os.path.join(LIBRARY_BASE_PATH, realm, "documents", "tsd")
        os.makedirs(kbd_dest, exist_ok=True)
        os.makedirs(tsd_dest, exist_ok=True)

        # Copy files
        copied_kbd = 0
        copied_tsd = 0
        for file in os.listdir(kbd_src):
            if file.endswith(".json"):
                shutil.copy(os.path.join(kbd_src, file), os.path.join(kbd_dest, file))
                copied_kbd += 1
        for file in os.listdir(tsd_src):
            if file.endswith(".json"):
                shutil.copy(os.path.join(tsd_src, file), os.path.join(tsd_dest, file))
                copied_tsd += 1

        # Run embed_from_files.py as a subprocess
        try:
            result = subprocess.run(
                ["python", "backend/embed_from_files.py", "--realm", realm],
                check=True,
                capture_output=True,
                text=True,
            )
            print("🔁 Embed Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("❌ Embed Error:", e.stderr)
            return {
                "message": f"⚠️ Synced {copied_kbd} KBDs and {copied_tsd} TSDs to Realm '{realm}', but embedding failed."
            }

        return {
            "message": f"✅ Imported {copied_kbd} KBDs and {copied_tsd} TSDs into Realm '{realm}' and re-embedded successfully."
        }

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to clone the repository.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
