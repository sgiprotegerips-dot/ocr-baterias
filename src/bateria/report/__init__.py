"""Informe diagnóstico HTML imprimible (32+ páginas carta)."""


def generate_printable_report_html(report_data):
    from .builder import generate_printable_report_html as _gen

    return _gen(report_data)


__all__ = ["generate_printable_report_html"]
