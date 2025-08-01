"""Analyze transactions API endpoint."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
import io
import pandas as pd
from pathlib import Path
import os
import uuid
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Import the universal parser
from universal_parser import parse_universal_pdf

router = APIRouter(prefix="/api", tags=["analyze"])

from pydantic import BaseModel

class AnalyzeTransactionsRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


def analyze_transactions(transactions: List[Dict]) -> Dict[str, Any]:
    """Analyze transactions and generate insights"""
    if not transactions:
        return {
            "summary": {
                "total_transactions": 0,
                "total_deposits": 0,
                "total_withdrawals": 0,
                "net_change": 0,
                "average_transaction": 0
            },
            "categories": {},
            "monthly_breakdown": {},
            "top_merchants": [],
            "spending_patterns": {},
            "alerts": []
        }
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(transactions)
    
    # Calculate summary statistics
    deposits = df[df['amount'] > 0]['amount'].sum() if 'amount' in df.columns else 0
    withdrawals = abs(df[df['amount'] < 0]['amount'].sum()) if 'amount' in df.columns else 0
    
    summary = {
        "total_transactions": len(transactions),
        "total_deposits": round(float(deposits), 2),
        "total_withdrawals": round(float(withdrawals), 2),
        "net_change": round(float(deposits - withdrawals), 2),
        "average_transaction": round(float(df['amount'].mean()) if 'amount' in df.columns else 0, 2),
        "date_range": {
            "start": df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns and not df['date'].empty else None,
            "end": df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns and not df['date'].empty else None
        }
    }
    
    # Categorize transactions
    categories = categorize_transactions(df)
    
    # Monthly breakdown
    monthly_breakdown = {}
    if 'date' in df.columns:
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly = df.groupby('month').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        
        for month, data in monthly.iterrows():
            monthly_breakdown[str(month)] = {
                "total": float(data[('amount', 'sum')]),
                "count": int(data[('amount', 'count')]),
                "average": float(data[('amount', 'mean')])
            }
    
    # Top merchants/descriptions
    top_merchants = []
    if 'description' in df.columns:
        merchant_spending = df[df['amount'] < 0].groupby('description')['amount'].agg(['sum', 'count'])
        merchant_spending['sum'] = abs(merchant_spending['sum'])
        top_10 = merchant_spending.nlargest(10, 'sum')
        
        for desc, data in top_10.iterrows():
            top_merchants.append({
                "merchant": desc,
                "total_spent": round(float(data['sum']), 2),
                "transaction_count": int(data['count'])
            })
    
    # Spending patterns
    spending_patterns = analyze_spending_patterns(df)
    
    # Generate alerts
    alerts = generate_alerts(df, summary)
    
    return {
        "summary": summary,
        "categories": categories,
        "monthly_breakdown": monthly_breakdown,
        "top_merchants": top_merchants,
        "spending_patterns": spending_patterns,
        "alerts": alerts
    }


def categorize_transactions(df: pd.DataFrame) -> Dict[str, Dict]:
    """Categorize transactions based on description patterns"""
    categories = {
        "Food & Dining": ["restaurant", "cafe", "coffee", "food", "pizza", "burger", "starbucks", "mcdonalds", "subway"],
        "Shopping": ["amazon", "walmart", "target", "store", "mall", "shop"],
        "Transportation": ["uber", "lyft", "gas", "fuel", "parking", "toll"],
        "Entertainment": ["netflix", "spotify", "movie", "theater", "game", "music"],
        "Utilities": ["electric", "water", "gas", "internet", "phone", "utility"],
        "Healthcare": ["pharmacy", "doctor", "hospital", "medical", "health"],
        "ATM & Cash": ["atm", "withdrawal", "cash"],
        "Transfers": ["transfer", "payment", "deposit", "credit"],
        "Other": []
    }
    
    category_totals = {cat: {"total": 0, "count": 0, "transactions": []} for cat in categories}
    
    if 'description' not in df.columns:
        return category_totals
    
    for _, trans in df.iterrows():
        desc = str(trans.get('description', '')).lower()
        amount = float(trans.get('amount', 0))
        categorized = False
        
        for category, keywords in categories.items():
            if category == "Other":
                continue
            if any(keyword in desc for keyword in keywords):
                category_totals[category]["total"] += abs(amount)
                category_totals[category]["count"] += 1
                category_totals[category]["transactions"].append({
                    "date": trans['date'].strftime('%Y-%m-%d') if 'date' in trans and pd.notna(trans['date']) else None,
                    "description": trans.get('description', ''),
                    "amount": amount
                })
                categorized = True
                break
        
        if not categorized:
            category_totals["Other"]["total"] += abs(amount)
            category_totals["Other"]["count"] += 1
            category_totals["Other"]["transactions"].append({
                "date": trans['date'].strftime('%Y-%m-%d') if 'date' in trans and pd.notna(trans['date']) else None,
                "description": trans.get('description', ''),
                "amount": amount
            })
    
    # Round totals and limit transactions
    for category in category_totals:
        category_totals[category]["total"] = round(category_totals[category]["total"], 2)
        category_totals[category]["transactions"] = category_totals[category]["transactions"][:5]  # Top 5 only
    
    return category_totals


def analyze_spending_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze spending patterns"""
    patterns = {
        "daily_average": 0,
        "weekend_vs_weekday": {"weekend": 0, "weekday": 0},
        "largest_expense": None,
        "most_frequent_amount": None
    }
    
    if df.empty or 'amount' not in df.columns:
        return patterns
    
    # Daily average spending
    if 'date' in df.columns:
        date_range = (df['date'].max() - df['date'].min()).days + 1
        if date_range > 0:
            patterns["daily_average"] = round(float(abs(df[df['amount'] < 0]['amount'].sum()) / date_range), 2)
        
        # Weekend vs weekday
        df['weekday'] = pd.to_datetime(df['date']).dt.dayofweek
        weekend_spending = abs(df[(df['weekday'] >= 5) & (df['amount'] < 0)]['amount'].sum())
        weekday_spending = abs(df[(df['weekday'] < 5) & (df['amount'] < 0)]['amount'].sum())
        patterns["weekend_vs_weekday"] = {
            "weekend": round(float(weekend_spending), 2),
            "weekday": round(float(weekday_spending), 2)
        }
    
    # Largest expense
    if len(df[df['amount'] < 0]) > 0:
        largest = df[df['amount'] < 0].nsmallest(1, 'amount').iloc[0]
        patterns["largest_expense"] = {
            "amount": round(float(abs(largest['amount'])), 2),
            "description": largest.get('description', 'Unknown'),
            "date": largest['date'].strftime('%Y-%m-%d') if 'date' in largest and pd.notna(largest['date']) else None
        }
    
    # Most frequent amount
    amount_counts = df['amount'].value_counts()
    if len(amount_counts) > 0:
        most_frequent = amount_counts.index[0]
        patterns["most_frequent_amount"] = {
            "amount": round(float(most_frequent), 2),
            "count": int(amount_counts.iloc[0])
        }
    
    return patterns


def generate_alerts(df: pd.DataFrame, summary: Dict) -> List[Dict]:
    """Generate financial alerts and insights"""
    alerts = []
    
    if df.empty or 'amount' not in df.columns:
        return alerts
    
    # Check for duplicate transactions
    if 'description' in df.columns and 'amount' in df.columns:
        duplicates = df[df.duplicated(subset=['description', 'amount'], keep=False)]
        if len(duplicates) > 0:
            alerts.append({
                "type": "warning",
                "title": "Possible Duplicate Transactions",
                "message": f"Found {len(duplicates)} possible duplicate transactions that might need review."
            })
    
    # High spending alert
    if summary['total_withdrawals'] > summary['total_deposits'] * 1.1:
        alerts.append({
            "type": "danger",
            "title": "Spending Exceeds Income",
            "message": f"Your spending (${summary['total_withdrawals']:,.2f}) exceeds deposits by ${summary['total_withdrawals'] - summary['total_deposits']:,.2f}"
        })
    
    # Large transactions alert
    if 'amount' in df.columns:
        avg_withdrawal = abs(df[df['amount'] < 0]['amount'].mean()) if len(df[df['amount'] < 0]) > 0 else 0
        large_transactions = df[df['amount'] < (-3 * avg_withdrawal)]
        if len(large_transactions) > 0:
            alerts.append({
                "type": "info",
                "title": "Large Transactions Detected",
                "message": f"Found {len(large_transactions)} transactions significantly above your average spending"
            })
    
    # Positive balance trend
    if summary['net_change'] > 0:
        alerts.append({
            "type": "success",
            "title": "Positive Cash Flow",
            "message": f"Great job! You saved ${summary['net_change']:,.2f} during this period"
        })
    
    return alerts


@router.post("/analyze-transactions")
async def analyze_transactions_endpoint(file: UploadFile = File(...)):
    """Analyze PDF bank statement and return financial insights"""
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file temporarily
    upload_dir = Path(__file__).parent.parent.parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}.pdf"
    
    try:
        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Extract transactions using universal parser
        transactions = parse_universal_pdf(str(file_path))
        
        if not transactions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transactions found in the PDF"
            )
        
        # Analyze transactions
        analysis = analyze_transactions(transactions)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "transaction_count": len(transactions),
                "analysis": analysis,
                "transactions": transactions  # Include transactions for export
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path.exists():
            os.remove(file_path)


def generate_pdf_report(analysis: Dict[str, Any]) -> bytes:
    """Generate a PDF report from analysis results"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("Financial Analysis Report", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Summary Section
    story.append(Paragraph("Summary", styles['Heading2']))
    summary = analysis['summary']
    summary_data = [
        ['Total Transactions:', str(summary['total_transactions'])],
        ['Total Deposits:', f"${summary['total_deposits']:,.2f}"],
        ['Total Withdrawals:', f"${summary['total_withdrawals']:,.2f}"],
        ['Net Change:', f"${summary['net_change']:,.2f}"],
        ['Average Transaction:', f"${summary['average_transaction']:,.2f}"],
    ]
    
    if summary.get('date_range'):
        summary_data.append(['Date Range:', f"{summary['date_range']['start']} to {summary['date_range']['end']}"])
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Category Breakdown
    story.append(Paragraph("Spending by Category", styles['Heading2']))
    categories = analysis['categories']
    category_data = [['Category', 'Amount', 'Count']]
    
    for cat, data in sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True):
        if data['total'] > 0:
            category_data.append([cat, f"${data['total']:,.2f}", str(data['count'])])
    
    if len(category_data) > 1:
        category_table = Table(category_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4facfe')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(category_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Top Merchants
    if analysis.get('top_merchants'):
        story.append(Paragraph("Top Merchants", styles['Heading2']))
        merchant_data = [['Merchant', 'Total Spent', 'Transactions']]
        
        for merchant in analysis['top_merchants'][:10]:
            merchant_data.append([
                merchant['merchant'][:40] + '...' if len(merchant['merchant']) > 40 else merchant['merchant'],
                f"${merchant['total_spent']:,.2f}",
                str(merchant['transaction_count'])
            ])
        
        merchant_table = Table(merchant_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        merchant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4facfe')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(merchant_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_excel_report(analysis: Dict[str, Any], transactions: List[Dict]) -> bytes:
    """Generate an Excel report from analysis results"""
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Summary Sheet
        summary_df = pd.DataFrame({
            'Metric': ['Total Transactions', 'Total Deposits', 'Total Withdrawals', 'Net Change', 'Average Transaction'],
            'Value': [
                analysis['summary']['total_transactions'],
                f"${analysis['summary']['total_deposits']:,.2f}",
                f"${analysis['summary']['total_withdrawals']:,.2f}",
                f"${analysis['summary']['net_change']:,.2f}",
                f"${analysis['summary']['average_transaction']:,.2f}"
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Transactions Sheet
        if transactions:
            trans_df = pd.DataFrame(transactions)
            trans_df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Categories Sheet
        categories_data = []
        for cat, data in analysis['categories'].items():
            if data['total'] > 0:
                categories_data.append({
                    'Category': cat,
                    'Total': data['total'],
                    'Count': data['count']
                })
        
        if categories_data:
            categories_df = pd.DataFrame(categories_data)
            categories_df.to_excel(writer, sheet_name='Categories', index=False)
        
        # Monthly Breakdown Sheet
        if analysis['monthly_breakdown']:
            monthly_data = []
            for month, data in analysis['monthly_breakdown'].items():
                monthly_data.append({
                    'Month': month,
                    'Total': data['total'],
                    'Count': data['count'],
                    'Average': data['average']
                })
            
            monthly_df = pd.DataFrame(monthly_data)
            monthly_df.to_excel(writer, sheet_name='Monthly Analysis', index=False)
        
        # Top Merchants Sheet
        if analysis['top_merchants']:
            merchants_df = pd.DataFrame(analysis['top_merchants'])
            merchants_df.to_excel(writer, sheet_name='Top Merchants', index=False)
        
        # Format the workbook
        workbook = writer.book
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4facfe',
            'font_color': 'white'
        })
        
        currency_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        # Apply formats to all sheets
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            # This would require openpyxl specific formatting
    
    buffer.seek(0)
    return buffer.read()


@router.post("/generate-pdf-report")
async def generate_pdf_report_endpoint(analysis_data: Dict[str, Any]):
    """Generate PDF report from analysis data"""
    try:
        pdf_bytes = generate_pdf_report(analysis_data)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=financial_analysis_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )


@router.post("/generate-excel-report")
async def generate_excel_report_endpoint(report_data: Dict[str, Any]):
    """Generate Excel report from analysis data"""
    try:
        analysis = report_data.get('analysis', {})
        transactions = report_data.get('transactions', [])
        
        excel_bytes = generate_excel_report(analysis, transactions)
        
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=financial_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Excel: {str(e)}"
        )


@router.post("/analyze-transactions-filtered")
async def analyze_transactions_filtered(
    transactions: List[Dict[str, Any]],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Analyze transactions with optional date filtering"""
    
    # Filter transactions by date if provided
    if start_date or end_date:
        filtered_transactions = []
        for trans in transactions:
            # Try to parse date from transaction
            trans_date = None
            if 'date' in trans:
                try:
                    if isinstance(trans['date'], str):
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                            try:
                                trans_date = datetime.strptime(trans['date'], fmt)
                                break
                            except:
                                continue
                    elif isinstance(trans['date'], datetime):
                        trans_date = trans['date']
                except:
                    pass
            
            # Apply date filter
            if trans_date:
                if start_date and trans_date < start_date:
                    continue
                if end_date and trans_date > end_date:
                    continue
                filtered_transactions.append(trans)
        
        transactions = filtered_transactions
    
    # Analyze the filtered transactions
    analysis = analyze_transactions(transactions)
    
    return {
        "analysis": analysis,
        "filtered_count": len(transactions),
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }
    }