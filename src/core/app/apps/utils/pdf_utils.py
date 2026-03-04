import io
import logging
import os
import tempfile

import pdfkit
from django.core.files import File
from django.template.loader import render_to_string

from apps.utils.number_utils import number_format

logger = logging.getLogger(__name__)


class PDFUtils:
    def __init__(
        self,
        company: object,
        template: str,
        context: dict,
        is_landscape=False,
        footer_template="footer.html",
    ):
        self.company = company
        self.context = context
        self.template = f"pdf/{template}"
        self.is_landscape = is_landscape
        self.footer_template = f"pdf/{footer_template}"

    def gen(self, filename: str):
        ctx = {"company": self.company}
        ctx.update(self.context)
        options = {
            "encoding": "utf-8",
            "orientation": "Landscape" if self.is_landscape else "Portrait",
            "enable-local-file-access": None,
            "load-error-handling": "ignore",
            "load-media-error-handling": "ignore",
            "margin-bottom": "25mm",
        }

        footer_path = None
        main_path = None
        try:
            # Write footer to temp file
            footer_html_content = render_to_string(self.footer_template).encode("utf-8")
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as footer_file:
                footer_file.write(footer_html_content)
                footer_path = footer_file.name
            options["footer-html"] = footer_path

            # Write main HTML to temp file (footer-html works better with from_file)
            main_html = render_to_string(self.template, ctx)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as main_file:
                main_file.write(main_html)
                main_path = main_file.name

            pdf = pdfkit.from_file(main_path, output_path=False, options=options)
            return File(io.BytesIO(pdf), name=filename)

        finally:
            if footer_path and os.path.exists(footer_path):
                os.remove(footer_path)
            if main_path and os.path.exists(main_path):
                os.remove(main_path)

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
            html.append("</tr>")

        html.append("</table>")
        ctx = {"body": "".join(html)}
        ctx.update(self.context)
        self.context = ctx
        return self.gen(filename)
