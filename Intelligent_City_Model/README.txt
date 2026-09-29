1. Esta Build incluye las carpetas de "BUILD" donde contiene los scripts dependientes del Arduino y el script de programacion del mismo.
2. La carpeta "TESTS" incluye scripts para pruebas de deteccion tanto con el modelo antiguo como con YOLO v4 y YOLO v8, asi como pruebas sonoras.
3. El script principal a correr con Python es "Main_YOLOV.py" en la carpeta "BUILD".
4. La carpeta YOLO incluye los archivos con los binarios para que PyTorch lo detecte, es possible que no sea visualizable en VS Code.
5. Los archivos .names, .cfg y .weights son para el modelo de deteccion YOLO V4 tiny, corre con CPU, sin embargo puede llegar a ser demandante para y esta y generar cuellos de botella con programas en segundo plano.


