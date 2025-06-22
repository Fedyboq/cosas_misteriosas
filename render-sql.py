import json
import tempfile
import os
from eralchemy2 import render_er
from base64 import b64encode

def lambda_handler(event, context):
    try:
        # Obtener el JSON del cuerpo de la solicitud
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No se proporcionó JSON en el cuerpo'})
            }
        
        # Parsear el JSON (puede venir como string si es una solicitud HTTP API)
        if isinstance(event['body'], str):
            data = json.loads(event['body'])
        else:
            data = event['body']
        
        # Validar datos básicos
        if not data or 'entities' not in data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'JSON inválido o falta sección "entities"'})
            }
        
        # Crear archivos temporales
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_input:
            temp_input.write(generate_er_script(data))
            temp_input_path = temp_input.name
        
        temp_output = tempfile.NamedTemporaryFile(suffix='.svg', delete=False)
        temp_output.close()
        temp_output_path = temp_output.name
        
        # Generar el diagrama
        render_er(temp_input_path, temp_output_path)
        
        # Leer el SVG generado
        with open(temp_output_path, 'rb') as svg_file:
            svg_content = svg_file.read()
        
        # Limpiar archivos temporales
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        
        # Codificar el SVG en base64 para la respuesta
        svg_base64 = b64encode(svg_content).decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/svg+xml',
                'Content-Disposition': 'attachment; filename="diagrama_er.svg"'
            },
            'body': svg_base64,
            'isBase64Encoded': True
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_er_script(data):
    """Genera el script de ERAlchemy a partir del JSON"""
    er_script = ""
    
    # Procesar entidades
    for entity in data.get('entities', []):
        er_script += f"{entity['name']} {{\n"
        for attr in entity.get('attributes', []):
            er_script += f"    {attr['name']} {attr['type']}"
            if attr.get('primary_key', False):
                er_script += " PK"
            if attr.get('nullable', True) is False:
                er_script += " NOT NULL"
            er_script += "\n"
        er_script += "}\n\n"
    
    # Procesar relaciones
    for relation in data.get('relations', []):
        left_card = relation.get('cardinality1', '')
        right_card = relation.get('cardinality2', '')
        er_script += f"{relation['entity1']} {left_card} -- {right_card} {relation['entity2']}\n"
    
    return er_script
