"""Static research histogram using ReportLab's chart renderer and PDFium."""
from pathlib import Path
import sys

import pandas as pd
import pypdfium2 as pdfium
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.lib.colors import HexColor, white


def main():
    out = Path(sys.argv[1])
    data = pd.read_csv(out/'distribution.csv')
    d = data.loc[data['sample'].eq('momentum_top20') & data.weighting.eq('all') & data.period.eq('all')]
    stock = d.loc[d.metric.eq('stock_return')]
    spy = d.loc[d.metric.eq('spy_return')]
    summary = pd.read_csv(out/'summary.csv')
    s = summary.loc[summary['sample'].eq('momentum_top20') & summary.weighting.eq('all') & summary.period.eq('all')].iloc[0]
    drawing = Drawing(1200, 650)
    drawing.add(Rect(0, 0, 1200, 650, fillColor=white, strokeColor=None))
    drawing.add(String(60, 610, 'Annual return distribution after ATH', fontName='Helvetica-Bold', fontSize=25))
    drawing.add(String(60, 581, f'ATH + 6-1 momentum top20 | {int(s.events):,} events | 252 holding sessions', fontSize=14))
    drawing.add(String(60, 550, f'Stock mean {s.stock:+.2%}   |   Median {s["median"]:+.2%}   |   Negative annual return: {s.loss:.2%}', fontSize=14))
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 80, 180, 1060, 310
    chart.data = [tuple(stock.fraction*100), tuple(spy.fraction*100)]
    chart.categoryAxis.categoryNames = stock['bin'].tolist()
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.boxAnchor = 'ne'
    chart.categoryAxis.labels.fontSize = 11
    chart.valueAxis.valueMin = 0
    highest = max(stock.fraction.max(), spy.fraction.max())*100
    chart.valueAxis.valueMax = (int(highest/5)+2)*5
    chart.valueAxis.valueStep = 5
    chart.valueAxis.labels.fontSize = 11
    chart.bars[0].fillColor = HexColor('#1565c0')
    chart.bars[1].fillColor = HexColor('#90a4ae')
    chart.bars.strokeColor = None
    chart.barLabelFormat = '%.1f'
    chart.barLabels.fontSize = 9
    chart.groupSpacing = 14
    drawing.add(chart)
    drawing.add(String(22, 500, 'Events (%)', fontSize=12))
    drawing.add(Rect(80, 104, 17, 12, fillColor=HexColor('#1565c0'), strokeColor=None))
    drawing.add(String(105, 104, 'ATH stock', fontSize=12))
    drawing.add(Rect(245, 104, 17, 12, fillColor=HexColor('#90a4ae'), strokeColor=None))
    drawing.add(String(270, 104, 'SPY over the same event windows', fontSize=12))
    drawing.add(String(60, 66, 'All return tails are included. Bins include the lower endpoint and exclude the upper endpoint.', fontSize=11))
    drawing.add(String(60, 45, 'Gross event returns with distributions and terminal cash; overlapping signals. This is not a portfolio or stop-loss backtest.', fontSize=11))
    document = pdfium.PdfDocument(renderPDF.drawToString(drawing))
    bitmap = document[0].render(scale=1.5)
    bitmap.to_pil().save(out/'return_distribution.png')
    print(out/'return_distribution.png')


if __name__ == '__main__':
    main()
