from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os 
import boto3
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = os.urandom(24) 
BUCKET = ''  # your bucket name


@app.route('/', methods=['GET'])
def get_index():
    try:
        if session.get('autenticado'):
            return redirect(url_for('explore'))
        else:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # NOT A REAL LOGIN LOGIC
        user = request.form['user']
        password = request.form['password']
        if user == 's3-admin@root.com' and password == '1423':
            session['autenticado'] = True
            return redirect(url_for('get_upload_template'))
        else:
            return render_template('login.html')
    else: 
        return render_template('login.html')
    
@app.route('/upload', methods=['GET'])
def get_upload_template():
    try:
        if session.get('autenticado'):
            return render_template('drag_and_drop.html') 
    except:
        return render_template('login.html')

@app.route('/explore')
def index():
    if session.get('autenticado'):
        root_directories = list_s3_directories(BUCKET)
        return render_template('download.html', directories=root_directories)
    else:
        return render_template('login.html')

@app.route('/api/upload-photos', methods=['POST']) 
def upload_photos():
    try:
        if session.get('autenticado'):
            respuesta = recepciona_fotos(app, request, BUCKET) 
            return respuesta
    except:
        return 'You are not auth', 403

@app.route('/api/list_objects', methods=['POST'])
def api_list_objects():
    try:
        if session.get('autenticado'):
            data = request.get_json()
            prefix = data.get('prefix', '')
            objects = list_s3_objects(BUCKET, prefix)
            return jsonify(objects)
    except:
        return 'You are not auth', 403

@app.route('/api/object', methods=['GET'])
def get_objects():
    try:
        if session.get('autenticado'):
            url = get_object_url(request.args.get('name'), BUCKET)
            return jsonify({'url': url})
    except:
        return 'You are not auth', 403
    
@app.route('/api/s3_usage')
def s3_usage():
    try:
        if session.get('autenticado'):
            ce = boto3.client('ce')  
            today = datetime.utcnow()
            start = today.replace(day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')

            cost_response = ce.get_cost_and_usage(
                TimePeriod={'Start': start, 'End': end},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Simple Storage Service']
                    }
                }
            )
            current_cost = float(cost_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

            days_passed = today.day
            days_total = calendar.monthrange(today.year, today.month)[1]
            estimated_cost = round((current_cost / days_passed) * days_total, 2) if days_passed > 0 else 0.0

            usage_response = ce.get_usage(
                TimePeriod={'Start': start, 'End': end},
                Granularity='MONTHLY',
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Simple Storage Service']
                    }
                },
                Metrics=['UsageQuantity'],
                GroupBy=[{
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }]
            )

            usage_gb = 0.0
            for group in usage_response['ResultsByTime'][0]['Groups']:
                usage_type = group['Keys'][0]
                if 'TimedStorage-ByteHrs' in usage_type:  
                    usage_hours = float(group['Metrics']['UsageQuantity']['Amount'])
                    usage_gb = round(usage_hours / 744, 2)  # horas mensuales -> GB estimado

            return jsonify({
                'current_usage_gb': usage_gb,
                'current_cost': round(current_cost, 2),
                'estimated_cost_end_month': estimated_cost
            })
    except:
        return 'You are not auth', 403

def recepciona_fotos(app, request, BUCKET):
    if 'images[]' not in request.files:
        return jsonify({'error': 'No se encontraron archivos.'}), 400

    images = request.files.getlist('images[]')
    saved_files = []
    s3 = boto3.client('s3')

    for image in images:
        if image.filename == '':
            continue
        filename = image.filename  # Puedes usar secure_filename si quieres sanitizar
        content_type = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'

        s3.put_object(
            Bucket=BUCKET,
            Key=f'originales/{filename}',  
            Body=image.stream,
            ContentType=content_type,
        )

        saved_files.append(filename)

    return jsonify({
        'message': f'{len(saved_files)} imagen(es) guardada(s) correctamente.',
        'files': saved_files
    })
    
def list_s3_objects(BUCKET, prefix=''):
    s3_client = boto3.client('s3')
    objects = []
    paginator = s3_client.get_paginator('list_objects_v2')

    try:
        response_iterator = paginator.paginate(Bucket=BUCKET, Prefix=prefix)
        for page in response_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if not obj['Key'].endswith('/'):
                        objects.append(obj['Key'])
        return sorted(objects)
    except Exception as e:
        print(f"Error al listar objetos: {e}")
        return []

def list_s3_directories(BUCKET, prefix=''):
    s3_client = boto3.client('s3')
    directories = set()
    paginator = s3_client.get_paginator('list_objects_v2')
    try:
        response_iterator = paginator.paginate(Bucket=BUCKET, Prefix=prefix, Delimiter='/')
        for page in response_iterator:
            if 'CommonPrefixes' in page:
                for common_prefix in page['CommonPrefixes']:
                    directories.add(common_prefix['Prefix'])
        return sorted(list(directories))
    except Exception as e:
        print(f"Error al listar directorios: {e}")
        return []

def get_object_url(object_name, BUCKET):
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET, 'Key': object_name},
        ExpiresIn=300  # válido por 5 minutos
    )
    return url

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')