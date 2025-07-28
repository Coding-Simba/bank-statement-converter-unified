"""Analyze transactions API endpoint."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, List, Any
from datetime import datetime
import io
import pandas as pd
from pathlib import Path
import os
import uuid
import json

# Import the universal parser
from universal_parser import parse_universal_pdf

router = APIRouter(prefix="/api", tags=["analyze"])


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
                "analysis": analysis
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