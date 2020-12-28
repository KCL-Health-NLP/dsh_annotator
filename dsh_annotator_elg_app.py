import traceback

from dsh_annotator import DSHAnnotator
from flask import Flask, request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from sys import exc_info


app = Flask(__name__)
# Don't add an extra "status" property to JSON responses - this would break the API contract
app.config['JSON_ADD_STATUS'] = False
# Don't sort properties alphabetically in response JSON
app.config['JSON_SORT_KEYS'] = False

json_app = FlaskJSON(app)


@json_app.invalid_json_error
def invalid_request_error(e):
    """Generates a valid ELG "failure" response if the request cannot be parsed"""
    raise JsonError(status_=400, failure={'errors': [
        {'code': 'elg.request.invalid', 'text': 'Invalid request message'}
    ]})


@app.route('/process', methods=['POST'])
@as_json
def process_request(self):
    """

    Return:
         - JSON response with all annotations.
    """

    data = request.get_json()
    # sanity checks on the request message
    if (data.get('type') != 'text') or ('content' not in data):
        invalid_request_error(None)

    content = data['content']

    try:
        dsha = DSHAnnotator(verbose=False)
        text_id = 'text_001'
        annotations = dsha.process_text(content, text_id, write_output=False, verbose=False)[text_id]
        ann_list = []

        for a in annotations:
            ann = {'start': a['start'],
                   'end': a['end'],
                   'features': {a.get(f, 'NONE') for f in a if f not in ['start', 'end']}
                }
            ann_list.append(ann)

        ann_dict = {'self-harm': ann_list}

        return dict(response={'type': 'annotations', 'annotations': ann_dict})

    except Exception:
        exc_type, exc_value, exc_traceback = exc_info()
        traceback.print_exc()
        # Convert any exception from the processing code into an ELG internal error
        raise JsonError(status_=500, failure={ 'errors': [
            {'code': 'elg.service.internalError', 'text': 'Internal error during processing: {0}',
             'params':[traceback.format_exception_only(exc_type, exc_value)[-1]]}
        ]})


if __name__ == '__main__':
    app.run()
