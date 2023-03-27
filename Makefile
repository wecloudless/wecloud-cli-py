obj:
	pyinstaller -D -F -n main -c "main.py"
	chmod +x dist/main