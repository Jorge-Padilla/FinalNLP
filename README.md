# FinalNLP

### Jorge Alberto Padilla Gutiérrez  A01635346
### Adrian Marcelo Suárez Ponce      A01197108
### Marcos Leroy Salazar Skinner     A01039743
### Jorge Antonio Ruiz Zavalza       A01411162
### Guillermo Sáenz González         A00823049

En este repositorio esta presente nuestro proyecto final de la materia de Procesamiento de Lenguaje Natural, en el que se implementó un modelo de Transformador Multimodal para predecir el éxito de venta de libros

## Descripción

Como objetivo, se debe implementar un modelo de Transformador Multimodal el cual sea capaz de trabajar con una mezcla de datos de texto, que son la base de la materia de Procesamiento de Lenguaje Natural, y datos tabulares, que estos pueden ser numericos o clases, y son los generales utilizados en el are de Aprendizaje Automático y Aprendizaje Profundo.

Para esto, elegimos desarrollar un modelo capaz de predecir el exito en ventas de los libros, el cual recibe como información de entrada el Título, la Descripción (que es el principal valor de texto), el precio, las paginas y la cantidad de reviews (siendo todos estos tabulares), e intenta predecir la cantidad de estrellas que este libro tendría publicado en las paginas de ventas de libros.

## Bases de Datos

La bases de datos investigada e incorporada para esta actividad integradora fue:

Kindle Books Dataset:
https://www.kaggle.com/snathjr/kindle-books-dataset

## Librerias

Las principales librerías que se utilizaron en este proyecto son multimodal-transformers, la cual es la base para el modelo, kaggle para trabajar con las bases de datos; tambien utilizamos streamlit y gcsfs para la interfaz de usuario interactiva

Toda la información referente a los requerimientos del ambiente estan presentes en el archivo requirements.txt, por lo que este se puede utilizar

```shell
pip install -r requirements.txt
```

## Desarrollo

El desarrollo de este proyecto comenzó teniendo como base el tutorial de Georgian Partners para implementar un modelo multimodal, el cual esta presente en https://colab.research.google.com/github/georgianpartners/Multimodal-Toolkit/blob/master/notebooks/text_w_tabular_classification.ipynb

## Utilidad

Este modelo sirve para ayudar a predecir el exito de ventas de los libros, considerando como han sido las evaluaciones de libros ya existentes en sitios web de ventas, con esto es posible que se tenga una idea de cual es la tendencia de libros actualmente segun su descripción, tamaño y precio, y con esto los escritores tendrian una idea mas clara de que es lo que le interesa a los lectores

## Uso

Para trabajar con este modelo de analisis de exito de libros, primero se debe clonar el repositorio, ya sea mediante la opcion de clone de la interfaz de GitHub o desde terminal
```shell
git clone https://github.com/Jorge-Padilla/FinalNLP
```

Presente en el archivo .ipynb se encuentran los recuadros de ejecución del modelo, y al final de estos los necesarios para la interfaz de usuario

### Modelo

Entre las primeras celdas del modelo se encuentra lo necesario para instalar y poder trabajar con Kaggle, principalmente el cuadro de adquisición del kaggle.json
```python
from google.colab import files
files.upload()
```

Donde se debe ingreasr el archivo kaggle.json para poder trabajar con sus bases de datos

Después estan presentes cuadros que muestran las graficas sobre información de los datasets, los cuales tienen visualizaciones de como se distribuyen estos en la base de datos. Con esto estan las celdas que preparan los datos para ser utilzados en el modelo

El modelo utilizado es "Bert Base Uncased", utilizando como combinador de features "Gating on categorical and numerical features then sum", y con task de "Regresión"

## Innovación: Interfaz de Usuario Interactiva

Como innovación en este proyecto se imlpementó una Interfaz de Usuario mediante Streamlit
