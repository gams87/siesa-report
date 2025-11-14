import io
import tempfile

import pdfkit
from django.core.files import File
from django.template.loader import render_to_string

from apps.utils.number_utils import number_format


class PDFUtils:
    def __init__(
        self,
        company: object,
        template: str,
        context: dict,
        is_landscape=False,
        footer_template=None,
    ):
        self.company = company
        self.context = context
        self.template = f"pdf/{template}"
        self.is_landscape = is_landscape
        self.footer_template = f"pdf/{footer_template}" if footer_template is not None else None

    def gen(self, filename: str):
        ctx = {"company": self.company}
        ctx.update(self.context)
        options = {
            "--encoding": "utf-8",
            "--orientation": "Landscape" if self.is_landscape else "Portrait",
            "--enable-local-file-access": None,
            "--load-error-handling": "ignore",
            "--load-media-error-handling": "ignore",
        }

        try:
            if self.footer_template:
                with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as footer_html:
                    # options['--footer-html'] = footer_html.name
                    # options['--footer-html'] = footer_html.name
                    footer_data = render_to_string(self.footer_template).encode("utf-8")
                    footer_html.write(footer_data)

            main_html = render_to_string(self.template, ctx)
            pdf = pdfkit.from_string(main_html, output_path=False, options=options)
            return File(io.BytesIO(pdf), name=filename)

        finally:
            if self.footer_template:
                # os.remove(options['--footer-html'])
                pass

    def gen_with_df(self, filename: str, df, columns_number=None):
        if columns_number is None:
            columns_number = []
        dict_data = [df.to_dict(), df.to_dict("index")]

        html = ['<table class="dataframe"><tr><th>#</th>']
        [html.append(f'<th class="header">{key}</th>') for key in dict_data[0].keys()]
        html.append("</tr>")

        for key in dict_data[1].keys():
            html.append(f'<tr><td class="index">{key + 1}</td>')
            for subkey in dict_data[1][key]:
                if subkey in columns_number:
                    value = number_format(dict_data[1][key][subkey])
                    html.append(f'<td style="text-align: end">{value}</td>')
                else:
                    html.append(f"<td>{dict_data[1][key][subkey]}</td>")

        html.append("</tr></table>")
        ctx = {"body": "".join(html)}
        ctx.update(self.context)
        self.context = ctx
        return self.gen(filename)
