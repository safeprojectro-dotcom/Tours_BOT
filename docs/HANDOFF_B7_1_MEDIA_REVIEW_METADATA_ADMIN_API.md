git status
.\.venv\Scripts\python.exe -m compileall app tests alembic
.\.venv\Scripts\python.exe -m pytest tests/unit/test_supplier_offer_b6_branded_preview.py tests/unit/test_supplier_offer_b5_packaging_review.py tests/unit/test_supplier_offer_b4_packaging.py -q

git add app/services app/schemas app/api tests
git status
git commit -m "feat: add supplier offer media review admin api"
git push