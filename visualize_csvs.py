#!/usr/bin/env python3
"""
CSV Visualizer Script
---------------------
Automatically finds, analyzes, and visualizes all CSV files in the target directory recursively.

Features:
- Auto-discovers all CSV files (excluding system/hidden files like ._* or __MACOSX).
- Infers date/time, numeric, categorical, and text columns automatically.
- Generates interactive Plotly charts embedded in a dark-mode HTML dashboard.
- Saves static PNG visualizations for each dataset (histograms, time-series, bar charts, heatmaps).
- Provides summary statistics and clean terminal output.

Usage:
    python3 visualize_csvs.py [--dir .] [--output-dir csv_visualization_output] [--open]
"""

import sys
import os
import glob
import re
import math
import json
import argparse
from pathlib import Path

# Automatic Conda environment detection if dependencies are missing in current python
def ensure_dependencies():
    try:
        import pandas
        import matplotlib
        import seaborn
        import plotly
        return True
    except ImportError:
        pass

    # Candidates for Conda python executables
    candidates = [
        os.path.expanduser("~/miniconda3/bin/python3"),
        os.path.expanduser("~/anaconda3/bin/python3"),
        "/opt/conda/bin/python3"
    ]
    # Check CONDA_PREFIX if set
    if "CONDA_PREFIX" in os.environ:
        candidates.insert(0, os.path.join(os.environ["CONDA_PREFIX"], "bin", "python3"))

    for candidate in candidates:
        if os.path.exists(candidate) and os.path.realpath(sys.executable) != os.path.realpath(candidate):
            os.execv(candidate, [candidate] + sys.argv)

ensure_dependencies()

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set default seaborn theme
sns.set_theme(style="darkgrid")
plt.rcParams.update({'figure.max_open_warning': 0})

def find_csv_files(search_dir):
    """Find all valid CSV files recursively under search_dir."""
    search_path = os.path.abspath(search_dir)
    all_csvs = []
    
    for root, dirs, files in os.walk(search_path):
        # Ignore output directories and hidden folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__MACOSX', 'node_modules', 'csv_visualization_output']]
        for file in files:
            if file.endswith('.csv') and not file.startswith('._'):
                full_path = os.path.join(root, file)
                all_csvs.append(full_path)
                
    return sorted(all_csvs)

def parse_and_categorize_columns(df):
    """Classify columns into datetime, numeric, categorical, or text."""
    date_cols = []
    num_cols = []
    cat_cols = []
    text_cols = []
    
    df_clean = df.copy()
    
    # Drop unnamed index columns if present
    unnamed_cols = [c for c in df_clean.columns if c.startswith('Unnamed:') or c.strip() == '']
    if unnamed_cols:
        df_clean = df_clean.drop(columns=unnamed_cols)
        
    for col in df_clean.columns:
        # Check for potential datetime column
        col_lower = str(col).lower()
        is_date = False
        if any(kw in col_lower for kw in ['date', 'time', 'timestamp', 'created_at', 'updated_at', 'first_seen', 'last_seen']):
            try:
                parsed = pd.to_datetime(df_clean[col], errors='coerce')
                if parsed.notna().sum() > 0.5 * len(df_clean):
                    df_clean[col] = parsed
                    date_cols.append(col)
                    is_date = True
            except Exception:
                pass
                
        if is_date:
            continue
            
        # Check numeric
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            # If numeric with very low unique values, check if categorical
            unique_cnt = df_clean[col].nunique(dropna=True)
            if unique_cnt <= 10 and unique_cnt < len(df_clean) * 0.1:
                cat_cols.append(col)
            else:
                num_cols.append(col)
        elif pd.api.types.is_bool_dtype(df_clean[col]):
            cat_cols.append(col)
        else:
            # String / object column
            unique_cnt = df_clean[col].nunique(dropna=True)
            if unique_cnt <= 25 or unique_cnt <= len(df_clean) * 0.3:
                cat_cols.append(col)
            else:
                text_cols.append(col)
                
    return df_clean, date_cols, num_cols, cat_cols, text_cols

def generate_static_plots(df, date_cols, num_cols, cat_cols, file_name, plots_dir):
    """Generate and save PNG plots for a dataset using Matplotlib & Seaborn."""
    os.makedirs(plots_dir, exist_ok=True)
    generated_pngs = []
    
    # 1. Time-series plot if date columns exist and numeric columns exist
    if date_cols and num_cols:
        primary_date = date_cols[0]
        df_sorted = df.sort_values(by=primary_date)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        plot_num_cols = num_cols[:5]  # limit to top 5 numeric cols for readability
        for col in plot_num_cols:
            ax.plot(df_sorted[primary_date], df_sorted[col], label=col, marker='o', markersize=3, linewidth=1.5)
            
        ax.set_title(f"Time Series Trend ({file_name})", fontsize=14, fontweight='bold', pad=12)
        ax.set_xlabel(primary_date)
        ax.set_ylabel("Value")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=30)
        plt.tight_layout()
        
        save_path = os.path.join(plots_dir, "time_series.png")
        plt.savefig(save_path, dpi=150)
        plt.close()
        generated_pngs.append("time_series.png")
        
    # 2. Distributions of Numeric Columns
    if num_cols:
        n_num = len(num_cols)
        cols_to_plot = num_cols[:9]  # max 9 for grid
        n_plots = len(cols_to_plot)
        rows = math.ceil(n_plots / 3)
        cols = min(n_plots, 3)
        
        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
        if n_plots == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        for idx, col in enumerate(cols_to_plot):
            sns.histplot(df[col].dropna(), ax=axes[idx], kde=True, color="#4F46E5")
            axes[idx].set_title(col, fontsize=11, fontweight='bold')
            axes[idx].set_xlabel('')
            
        # Hide extra subplots
        for idx in range(n_plots, len(axes)):
            fig.delaxes(axes[idx])
            
        plt.suptitle(f"Numeric Distributions ({file_name})", fontsize=14, fontweight='bold')
        plt.tight_layout()
        save_path = os.path.join(plots_dir, "numeric_distributions.png")
        plt.savefig(save_path, dpi=150)
        plt.close()
        generated_pngs.append("numeric_distributions.png")
        
    # 3. Correlation Heatmap
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig, ax = plt.subplots(figsize=(max(6, len(num_cols)*0.8), max(5, len(num_cols)*0.7)))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax, cbar=True)
        ax.set_title(f"Correlation Heatmap ({file_name})", fontsize=14, fontweight='bold', pad=12)
        plt.tight_layout()
        save_path = os.path.join(plots_dir, "correlation_heatmap.png")
        plt.savefig(save_path, dpi=150)
        plt.close()
        generated_pngs.append("correlation_heatmap.png")
        
    # 4. Categorical Bar Charts
    if cat_cols:
        n_cat = min(len(cat_cols), 6)
        rows = math.ceil(n_cat / 2)
        cols = min(n_cat, 2)
        
        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows))
        if n_cat == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        for idx, col in enumerate(cat_cols[:n_cat]):
            val_counts = df[col].value_counts().head(10)
            sns.barplot(x=val_counts.values, y=val_counts.index.astype(str), ax=axes[idx], palette="viridis")
            axes[idx].set_title(f"Top Values: {col}", fontsize=11, fontweight='bold')
            axes[idx].set_xlabel('Count')
            
        for idx in range(n_cat, len(axes)):
            fig.delaxes(axes[idx])
            
        plt.suptitle(f"Categorical Frequencies ({file_name})", fontsize=14, fontweight='bold')
        plt.tight_layout()
        save_path = os.path.join(plots_dir, "categorical_counts.png")
        plt.savefig(save_path, dpi=150)
        plt.close()
        generated_pngs.append("categorical_counts.png")
        
    return generated_pngs

def generate_plotly_figures(df, date_cols, num_cols, cat_cols, file_name):
    """Generate interactive Plotly figures for HTML report."""
    figures = []
    
    # 1. Interactive Time Series
    if date_cols and num_cols:
        primary_date = date_cols[0]
        df_sorted = df.sort_values(by=primary_date)
        fig = go.Figure()
        for col in num_cols[:8]:  # Limit top 8 metrics
            fig.add_trace(go.Scatter(
                x=df_sorted[primary_date],
                y=df_sorted[col],
                mode='lines+markers',
                name=col
            ))
        fig.update_layout(
            title=f"📈 Time Series Analysis - {file_name}",
            xaxis_title=primary_date,
            yaxis_title="Value",
            template="plotly_dark",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=40)
        )
        figures.append({"title": "Time Series Trends", "html": fig.to_html(full_html=False, include_plotlyjs=False)})
        
    # 2. Correlation Matrix
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            title=f"🔥 Correlation Matrix - {file_name}",
            template="plotly_dark",
            aspect="auto"
        )
        fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
        figures.append({"title": "Correlation Matrix", "html": fig.to_html(full_html=False, include_plotlyjs=False)})
        
    # 3. Numeric Distributions / Box Plots
    if num_cols:
        fig = make_subplots(rows=1, cols=min(len(num_cols[:4]), 4), subplot_titles=num_cols[:4])
        for idx, col in enumerate(num_cols[:4]):
            fig.add_trace(go.Box(y=df[col].dropna(), name=col, boxmean='sd'), row=1, col=idx+1)
        fig.update_layout(
            title=f"📦 Box Plots & Range Distributions - {file_name}",
            template="plotly_dark",
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        figures.append({"title": "Numeric Distributions", "html": fig.to_html(full_html=False, include_plotlyjs=False)})

    # 4. Categorical Breakdown
    if cat_cols:
        primary_cat = cat_cols[0]
        val_counts = df[primary_cat].value_counts().head(12).reset_index()
        val_counts.columns = [primary_cat, 'count']
        fig = px.bar(
            val_counts,
            x=primary_cat,
            y='count',
            color='count',
            title=f"📊 Category Distribution: {primary_cat} - {file_name}",
            template="plotly_dark",
            color_continuous_scale="Viridis"
        )
        fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
        figures.append({"title": f"Category Breakdown ({primary_cat})", "html": fig.to_html(full_html=False, include_plotlyjs=False)})

    return figures

def build_html_dashboard(datasets_data, output_filepath):
    """Build a comprehensive, responsive HTML dashboard with embedded charts."""
    
    sidebar_tabs = ""
    tab_contents = ""
    
    for idx, ds in enumerate(datasets_data):
        active_class = "active" if idx == 0 else ""
        ds_id = f"ds_{idx}"
        file_name = ds['file_name']
        rel_path = ds['rel_path']
        
        # Sidebar Tab button
        sidebar_tabs += f"""
        <button class="tab-btn {active_class}" onclick="openTab(event, '{ds_id}')">
            <span class="file-icon">📄</span>
            <div class="tab-info">
                <span class="tab-title">{file_name}</span>
                <span class="tab-subtitle">{ds['rows']} rows • {ds['cols']} cols</span>
            </div>
        </button>
        """
        
        # Stat cards HTML
        stat_cards = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">File Path</div>
                <div class="stat-value code-path">{rel_path}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Rows</div>
                <div class="stat-value">{ds['rows']:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Columns</div>
                <div class="stat-value">{ds['cols']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Missing Values</div>
                <div class="stat-value">{ds['missing_count']} ({ds['missing_pct']:.1f}%)</div>
            </div>
        </div>
        """
        
        # Column breakdown badges
        col_badges = f"""
        <div class="badge-container">
            <span class="badge badge-date">📅 Date/Time ({len(ds['date_cols'])})</span>
            <span class="badge badge-num">🔢 Numeric ({len(ds['num_cols'])})</span>
            <span class="badge badge-cat">🏷️ Categorical ({len(ds['cat_cols'])})</span>
            <span class="badge badge-text">📝 Text/ID ({len(ds['text_cols'])})</span>
        </div>
        """
        
        # Interactive Plotly Charts
        charts_html = ""
        for fig_data in ds['plotly_figs']:
            charts_html += f"""
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{fig_data['title']}</h3>
                </div>
                <div class="chart-body">
                    {fig_data['html']}
                </div>
            </div>
            """
            
        # Data Preview Table
        preview_table_html = ds['preview_table_html']
        
        # PNG Images Gallery if generated
        png_gallery_html = ""
        if ds.get('png_files'):
            png_gallery_html += '<div class="gallery-title">Static PNG Visualizations</div><div class="png-gallery">'
            for png_name in ds['png_files']:
                png_rel = f"plots/{ds_id}/{png_name}"
                png_gallery_html += f"""
                <div class="png-card">
                    <img src="{png_rel}" alt="{png_name}" onclick="openModal(this.src)" />
                    <div class="png-caption">{png_name.replace('_', ' ').replace('.png', '').title()}</div>
                </div>
                """
            png_gallery_html += '</div>'

        tab_contents += f"""
        <div id="{ds_id}" class="tab-content {active_class}">
            <div class="dataset-header">
                <h2>{file_name}</h2>
                <div class="dataset-meta">{rel_path} • {ds['file_size_kb']:.1f} KB</div>
            </div>
            
            {stat_cards}
            {col_badges}
            
            <div class="section-title">📊 Interactive Data Charts</div>
            <div class="charts-grid">
                {charts_html}
            </div>
            
            {png_gallery_html}
            
            <div class="section-title">📋 Data Preview & Columns</div>
            <div class="table-container">
                {preview_table_html}
            </div>
        </div>
        """
        
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Data Visualizer Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-sidebar: #0b1120;
            --border-color: #334155;
            --accent-purple: #6366f1;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        
        /* Sidebar */
        .sidebar {{
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        
        .sidebar-header {{
            padding: 24px 20px;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
        }}
        
        .sidebar-header h1 {{
            font-size: 1.15rem;
            font-weight: 700;
            background: linear-gradient(90deg, #818cf8, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .sidebar-header p {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        
        .tab-list {{
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .tab-btn {{
            display: flex;
            align-items: center;
            gap: 12px;
            width: 100%;
            padding: 12px 14px;
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 10px;
            color: var(--text-muted);
            text-align: left;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .tab-btn:hover {{
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }}
        
        .tab-btn.active {{
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.2), rgba(99, 102, 241, 0.05));
            border-color: rgba(99, 102, 241, 0.4);
            color: #ffffff;
        }}
        
        .file-icon {{
            font-size: 1.2rem;
        }}
        
        .tab-info {{
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .tab-title {{
            font-size: 0.88rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .tab-subtitle {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        
        /* Main Content */
        .main-content {{
            flex: 1;
            overflow-y: auto;
            padding: 32px;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .dataset-header {{
            margin-bottom: 24px;
        }}
        
        .dataset-header h2 {{
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        
        .dataset-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            backdrop-filter: blur(10px);
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}
        
        .stat-value {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-main);
        }}
        
        .code-path {{
            font-size: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            word-break: break-all;
            color: #38bdf8;
        }}
        
        /* Badges */
        .badge-container {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 28px;
        }}
        
        .badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid transparent;
        }}
        
        .badge-date {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3); }}
        .badge-num {{ background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.3); }}
        .badge-cat {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }}
        .badge-text {{ background: rgba(14, 165, 233, 0.15); color: #38bdf8; border-color: rgba(14, 165, 233, 0.3); }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin: 32px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }}
        
        /* Charts Grid */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }}
        
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }}
        
        .chart-header {{
            padding: 14px 20px;
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
        }}
        
        .chart-header h3 {{
            font-size: 0.95rem;
            font-weight: 600;
        }}
        
        .chart-body {{
            padding: 10px;
        }}
        
        /* PNG Gallery */
        .gallery-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
            color: var(--text-muted);
        }}
        
        .png-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        
        .png-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }}
        
        .png-card img {{
            max-width: 100%;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        
        .png-card img:hover {{
            transform: scale(1.02);
        }}
        
        .png-caption {{
            margin-top: 8px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        
        /* Table */
        .table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow-x: auto;
            max-height: 450px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            text-align: left;
        }}
        
        th {{
            background: #0f172a;
            position: sticky;
            top: 0;
            padding: 12px 16px;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}
        
        td {{
            padding: 10px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            white-space: nowrap;
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.03);
        }}
        
        /* Modal for full image */
        .modal {{
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(5px);
            align-items: center;
            justify-content: center;
        }}
        
        .modal img {{
            max-width: 90%;
            max-height: 90%;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1>📊 CSV Analytics</h1>
            <p>Discovered {len(datasets_data)} Datasets</p>
        </div>
        <div class="tab-list">
            {sidebar_tabs}
        </div>
    </div>
    
    <div class="main-content">
        {tab_contents}
    </div>

    <div id="imgModal" class="modal" onclick="this.style.display='none'">
        <img id="modalImg" src="" alt="Full view" />
    </div>

    <script>
        function openTab(evt, tabId) {{
            let contents = document.getElementsByClassName("tab-content");
            for (let i = 0; i < contents.length; i++) {{
                contents[i].classList.remove("active");
            }}
            let buttons = document.getElementsByClassName("tab-btn");
            for (let i = 0; i < buttons.length; i++) {{
                buttons[i].classList.remove("active");
            }}
            document.getElementById(tabId).classList.add("active");
            evt.currentTarget.classList.add("active");
            window.dispatchEvent(new Event('resize'));
        }}
        
        function openModal(src) {{
            let modal = document.getElementById("imgModal");
            let img = document.getElementById("modalImg");
            img.src = src;
            modal.style.display = "flex";
        }}
    </script>
</body>
</html>
"""

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_template)

def main():
    parser = argparse.ArgumentParser(description="Visualize all CSV files in the workspace.")
    parser.add_argument("--dir", default=".", help="Directory to scan recursively for CSV files")
    parser.add_argument("--output-dir", default="csv_visualization_output", help="Directory to save output files")
    parser.add_argument("--open", action="store_true", help="Open generated HTML dashboard in browser")
    args = parser.parse_args()

    search_dir = os.path.abspath(args.dir)
    output_dir = os.path.abspath(args.output_dir)
    plots_base_dir = os.path.join(output_dir, "plots")
    
    print(f"\n=======================================================")
    print(f" 🔍 Scanning for CSV files in: {search_dir}")
    print(f"=======================================================\n")
    
    csv_files = find_csv_files(search_dir)
    
    if not csv_files:
        print("⚠️ No CSV files found under the current directory.")
        return

    print(f"Found {len(csv_files)} CSV dataset(s):\n")
    for idx, filepath in enumerate(csv_files, 1):
        rel = os.path.relpath(filepath, search_dir)
        size_kb = os.path.getsize(filepath) / 1024.0
        print(f"  {idx}. {rel} ({size_kb:.1f} KB)")
        
    print("\nProcessing datasets and generating visualizations...\n")
    
    datasets_data = []
    
    for idx, filepath in enumerate(csv_files):
        rel_path = os.path.relpath(filepath, search_dir)
        file_name = os.path.basename(filepath)
        ds_id = f"ds_{idx}"
        dataset_plots_dir = os.path.join(plots_base_dir, ds_id)
        
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"❌ Error reading {rel_path}: {e}")
            continue

        file_size_kb = os.path.getsize(filepath) / 1024.0
        rows, cols = df.shape
        missing_count = int(df.isna().sum().sum())
        total_cells = rows * cols if rows * cols > 0 else 1
        missing_pct = (missing_count / total_cells) * 100.0
        
        df_clean, date_cols, num_cols, cat_cols, text_cols = parse_and_categorize_columns(df)
        
        # Generate static PNG plots
        png_files = generate_static_plots(df_clean, date_cols, num_cols, cat_cols, file_name, dataset_plots_dir)
        
        # Generate interactive Plotly figures
        plotly_figs = generate_plotly_figures(df_clean, date_cols, num_cols, cat_cols, file_name)
        
        # HTML preview table of first 10 rows
        preview_df = df.head(10)
        preview_table_html = preview_df.to_html(classes="preview-table", index=False, na_rep="NaN")
        
        datasets_data.append({
            'ds_id': ds_id,
            'file_name': file_name,
            'rel_path': rel_path,
            'full_path': filepath,
            'file_size_kb': file_size_kb,
            'rows': rows,
            'cols': cols,
            'missing_count': missing_count,
            'missing_pct': missing_pct,
            'date_cols': date_cols,
            'num_cols': num_cols,
            'cat_cols': cat_cols,
            'text_cols': text_cols,
            'png_files': png_files,
            'plotly_figs': plotly_figs,
            'preview_table_html': preview_table_html
        })
        print(f"  ✓ Processed: {rel_path} ({rows} rows, {cols} cols)")

    # Output HTML file
    os.makedirs(output_dir, exist_ok=True)
    html_filepath = os.path.join(output_dir, "csv_visualizer_report.html")
    build_html_dashboard(datasets_data, html_filepath)
    
    print("\n=======================================================")
    print(" ✅ Visualization Complete!")
    print(f" 📄 Interactive Dashboard: {html_filepath}")
    print(f" 🖼️ Static Plots Saved:     {plots_base_dir}")
    print("=======================================================\n")
    
    if args.open:
        import webbrowser
        webbrowser.open(f"file://{html_filepath}")

if __name__ == "__main__":
    main()
