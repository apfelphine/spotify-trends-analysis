import os

from fastapi import APIRouter, UploadFile, HTTPException

from app.business.data_import import load_songs_from_csv, get_min_max_date

router = APIRouter(
    tags=["data"],
    prefix="/data"
)


@router.post("/import")
async def import_file(file: UploadFile) -> str:
    """
    Import spotify trend data from kaggle file
    (expected dataset: https://www.kaggle.com/datasets/asaniczka/top-spotify-songs-in-73-countries-daily-updated)
    """
    try:
        contents = file.file.read()
        with open("/tmp/" + file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=500, detail='Couldn\'t read file')
    finally:
        file.file.close()

    from_date, until_date = await load_songs_from_csv("/tmp/" + file.filename)
    os.remove("/tmp/" + file.filename)

    if from_date is not None and until_date is not None:
        return f"Successfully imported spotify trend data for {from_date} - {until_date}"

    return "No new data to import found."


@router.get("/imported-date-range")
def get_imported_date_range() -> dict:
    """Retrieve the date range in the currently imported spotify trend data"""
    return get_min_max_date()
