from flask import Flask, render_template, request, flash, redirect, url_for
from config import config 
import cv2
import numpy as np 
import json 
import secrets
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'app/static/img'

@app.route ('/', methods = ['GET', 'POST'])
def index():
    path_img = ('app/static/img/examen_evaluado.jpg')
    exa = cv2.imread(path_img)
    results = []
    #parte 3: 
    if request.method == 'POST':
        if 'generate_result' in request.form:
            with open ('app/static/json/coords_plantilla.json', 'r') as f:
                    coords = json.load(f)
            for i, coord in enumerate(coords, start=1):
                x1 = int(coord['x1'])
                y1 = int(coord['y1'])   
                x2 = int(coord['x2'])
                y2 = int(coord['y2'])
                        
                cut = exa[y1:y2, x1:x2]
                h, w = cut.shape[:2]
                
                sub_cuts = [
                    ('A', cut[:, 0:w//4]),               # Primer cuarto (izquierda)
                    ('B', cut[:, w//4:w//2]),            # Segundo cuarto
                    ('C', cut[:, w//2:(3*w)//4]),        # Tercer cuarto
                    ('D', cut[:, (3*w)//4:w])            # Último cuarto (derecha)
                ]   
                max_blue = 0
                selection = None
                
                for label, sub in sub_cuts:
                    hsv = cv2.cvtColor(sub, cv2.COLOR_BGR2HSV)
                    blue = cv2.inRange(hsv, (90, 50, 50), (144, 255, 255))
                    blue_rate = cv2.countNonZero(blue) / (sub.shape[0]*sub.shape[1])

                    if blue_rate > max_blue:
                        max_blue = blue_rate
                        selection = label  
                if selection is not None:
                    results.append({'pregunta': i, 'respuesta': selection})
                else:
                    results.append({'pregunta': i, 'respuesta': 'None'})  
            with open('app/static/json/examen_evaluado.json', 'w') as f:
                json.dump(results, f)
            
            flash ('resultados generados correctamente')
            return  redirect(url_for('index'))
        
        elif request.method == 'POST':
            if 'file' not in request.files:
                flash('No se encontro ninguna imagen', 'error')
                return redirect(request.url)
            file = request.files['file']
            
            if file.filename == '':
                flash('tu examen no tiene nombre', 'error')
                return redirect(request.url)
            
            path_final = os.path.join(app.config['UPLOAD_FOLDER'], 'examen_evaluado.jpg')
            os.makedirs(os.path.dirname(path_final), exist_ok=True)
            file.save(path_final)
                
            exam = cv2.imread(path_final)
            if exam is None:
                flash('No se logro cargar el examen', 'error')
            else:
                flash('Examen cargada correctamente')
            return redirect(url_for('index'))
        else:
            flash ('no se encontro ninguna imagen', 'error')
            return redirect (request.url)
        
    return render_template ('index.html', results=results)


@app.route('/coords', methods = ['GET','POST'])
def coords():
    path_img = ('app/static/img/correcto.jpg')
    exa = cv2.imread(path_img)
    results = []
    
    if request.method == 'POST':
        if 'generate_ans' in request.form:
            with open ('app/static/json/coords_plantilla.json', 'r') as f:
                coords = json.load(f)
            for i, coord in enumerate(coords, start=1):
                x1 = int(coord['x1'])   
                y1 = int(coord['y1'])   
                x2 = int(coord['x2'])
                y2 = int(coord['y2'])
                        
                cut = exa[y1:y2, x1:x2]
                h, w = cut.shape[:2]
                
                sub_cuts = [
                    ('A', cut[:, 0:w//4]),               # Primer cuarto (izquierda)
                    ('B', cut[:, w//4:w//2]),            # Segundo cuarto
                    ('C', cut[:, w//2:(3*w)//4]),        # Tercer cuarto
                    ('D', cut[:, (3*w)//4:w])            # Último cuarto (derecha)
                ]   
                max_blue = 0
                selection = None
                
                for label, sub in sub_cuts: 
                    hsv = cv2.cvtColor(sub, cv2.COLOR_BGR2HSV)
                    blue = cv2.inRange(hsv, (90, 50, 50), (144, 255, 255))
                    blue_rate = cv2.countNonZero(blue) / (sub.shape[0]*sub.shape[1])

                    if blue_rate > max_blue:
                        max_blue = blue_rate
                        selection = label  
                if selection is not None:
                    results.append({'pregunta': i, 'respuesta': selection})
                else:
                    results.append({'pregunta': i, 'respuesta': 'None'})  
            with open('app/static/json/examen_correcto.json', 'w') as f:
                json.dump(results, f)
            
            flash ('resultados generados correctamente')
            return  redirect(url_for('coords'))
        
        if 'generate_coords' in request.form:
        #parte 1: dibujar circulos para detectar donde iran los cuadrados, para esto
        #se uso una imagen donde estan marcadas todas las (a) en la hoja de respuestas
            path = ('app/static/img/plantilla.jpg')
            img = cv2.imread(path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(
                gray, 
                cv2.HOUGH_GRADIENT, 
                dp=1, 
                minDist=20, 
                param1=20, 
                param2=25, 
                minRadius=5, 
                maxRadius=15)        
            
            circles_blue = []
            # variable donde se guardan las coordenadas de los rectangulos
            rectangles_coor = []

            if circles is not None:
                circles = np.uint16(np.around(circles[0]))
                for x,y,r in circles:
                    cut = img[y-r:y+r, x-r:x+r]
                    if cut.shape[0] == 0 or cut.shape[1] == 0:
                        continue
                    
                    
                    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)
                    low_blue = (90, 50, 50)
                    up_blue = (140, 255, 255)
                    mask = cv2.inRange(hsv, low_blue, up_blue)
                    blue_rate = cv2.countNonZero(mask)/(cut.shape[0]*cut.shape[1])
                        
                    if blue_rate > 0.2:
                        circles_blue.append((x, y, r))
                        cv2.circle(img, (x, y), r, (0, 0, 255), 2)  # rojo BGR  
                        #parte 2: aqui se guardan las coordenadas por primera vez de los incisos (a) para ubicar los rectangulos manualmente
                
                        #coordenadas para los rectangulos, solo se uso una vez para dibujar los rectangulos
                        x1 = int(x - r - 7)
                        y1 = int(y - r - 2)
                        x2 = int(x + r + 110)
                        y2 = int(y + r + 2)
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
                        rectangles_coor.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})              
                    
                # se aplica un sort para guardar las coordenadas en orden
                #esto solamente se usa una vez para ordenar y guardar las coordenadas de los rectangulos
                def sort_by_column_y(rects):
                    def x_group(x): return round(x / 10) * 10
                    return sorted(rects, key=lambda r: (x_group(r['x1']), r['y1']))
                rectangles_coor = sort_by_column_y(rectangles_coor)
                
                    # aqui se guardan las coordenadas de los rectangulos en un archivo json
                with open('app/static/json/coords_plantilla.json', 'w') as f:
                    json.dump(rectangles_coor, f)
                    
                    # Dibujar los rectángulos ordenados, 
                for coord in rectangles_coor:
                    x1 = int(coord['x1'])
                    y1 = int(coord['y1'])   
                    x2 = int(coord['x2'])
                    y2 = int(coord['y2'])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
                    cv2.imwrite('app/static/img/rectangles.jpg', img)
                
                flash('Se guardaron correctamente las coordenadas')
                return redirect(url_for('coords'))
            else:
                flash ('No se guardaron las coordenadas')
                return redirect(url_for('coords'))
        
        if 'plant' not in request.files:
            flash('No se encontro ninguna imagen', 'error')
            return redirect(request.url)
        file = request.files['plant']

        if file.filename == '':
            flash('tu plantilla no tiene nombre', 'error')
            return redirect(request.url)
        
        if file: 
            path_final = os.path.join(app.config['UPLOAD_FOLDER'], 'plantilla.jpg')
            os.makedirs(os.path.dirname(path_final), exist_ok=True)
            file.save(path_final)
            
        plantilla = cv2.imread(path_final)
        if plantilla is None:
            flash('No se logro cargar la plantilla', 'error')
        else:
            flash('Imagen cargada correctamente')
        return redirect(url_for('coords'))
    
    return render_template ('upload.html')


@app.route('/ans', methods = ['GET','POST'])
def ans():
    
    if request.method == 'POST':

        if 'correcto' not in request.files:
            flash('No se encontro ninguna imagen', 'error')
            return redirect(request.url)
        ans = request.files['correcto']

        if ans.filename == '':
            flash('tu examen correcto no tiene nombre', 'error')
            return redirect(request.url)

        if ans: 
            path_ans = os.path.join(app.config['UPLOAD_FOLDER'], 'correcto.jpg')
            os.makedirs(os.path.dirname(path_ans), exist_ok=True)
            ans.save(path_ans)

        plant_ans = cv2.imread(path_ans)
        if plant_ans is None:
            flash('No se logro cargar la plantilla', 'error')
        else:
            flash('Imagen cargada correctamente')
            
        return redirect(url_for('coords')) 

@app.route('/calif', methods = ['GET','POST'])
def calif():
    
    if request.method == 'POST':
        if 'calif_exam' in  request.form:
            with open('app/static/json/examen_correcto.json', 'r') as f1, open('app/static/json/examen_evaluado.json', 'r') as f2:
                answers = json.load(f2)
                correct = json.load(f1)
            comparacion = []
            correctas = 0
            incorrectas = 0
            
            for p_correct, p_ans in zip(answers, correct):
                result = {
                    'pregunta': p_correct['pregunta'],
                    'respuesta_correcta': p_correct['respuesta'],
                    'respuesta_usuario': p_ans['respuesta'],
                    'es_correcta': p_correct['respuesta'] == p_ans['respuesta']
                }
                comparacion.append(result)
                
                if result['es_correcta']:
                    correctas += 1
                else:
                    incorrectas += 1
                
            with open('app/static/json/comparacion.json', 'w') as f_out:
                    json.dump(comparacion, f_out)
        
        
        total_preguntas = correctas + incorrectas
        react = 10.0 / total_preguntas
        calificacion = react * correctas
        if calificacion < 6.0:
            calificacion = 5.0

        flash('Resultados de la calificacion generados correctamente')
        return render_template('index.html', correctas=correctas, incorrectas=incorrectas, calificacion=calificacion)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True) 