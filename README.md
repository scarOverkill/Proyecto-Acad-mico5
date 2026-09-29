[README.txt](https://github.com/user-attachments/files/32826014/README.txt)
Intelligent_City_Model
1. Esta Build incluye las carpetas de "BUILD" donde contiene los scripts dependientes del Arduino y el script de programacion del mismo.
2. La carpeta "TESTS" incluye scripts para pruebas de deteccion tanto con el modelo antiguo como con YOLO v4 y YOLO v8, asi como pruebas sonoras.
3. El script principal a correr con Python es "Main_YOLOV.py" en la carpeta "BUILD".
4. La carpeta YOLO incluye los archivos con los binarios para que PyTorch lo detecte, es possible que no sea visualizable en VS Code.
5. Los archivos .names, .cfg y .weights son para el modelo de deteccion YOLO V4 tiny, corre con CPU, sin embargo puede llegar a ser demandante para y esta y generar cuellos de botella con programas en segundo plano.

[README.txt](https://github.com/user-attachments/files/32826036/README.txt)
Intelligent_City_Model -1080p_Version
1. Esta Build incluye las carpetas de "BUILD" donde contiene los scripts del programa y un script para determiner la lista de microfonos detectados en las conexiones.
2. La carpeta "TESTS" incluye scripts para pruebas de deteccion para pruebas sonoras, OpenCV, YOLO, asi como pruebas sonoras sin necesidad de Arduino.
3. La carpeta YOLO incluye los archivos con los binarios para que PyTorch lo detecte, es posible que no sea visualizable en VS Code.
4. Esta Build tiene la camara configurada para que utilice toda su capacidad, a 1080p. Lo que puede ser mas demandante para la GPU, importante tomarlo en consideracion.


