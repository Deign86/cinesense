"""
CineSense Chart Generator
=========================

Demonstrates:
- Matplotlib charts (bar, histogram, line, pie)
- NumPy arrays for data processing
- For loops for data iteration
- Classes with __init__ and methods
- Custom iterators for chart generation
- f-strings for labels
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
import uuid
from datetime import datetime


class ChartGenerator:
    """
    Generate various charts for movie analytics.
    
    Demonstrates: Classes, __init__, methods with self,
                 Matplotlib chart creation
    """
    
    def __init__(self, output_dir: Path = None, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize chart generator.
        
        Demonstrates: __init__ method, default parameters, Path handling
        """
        self.output_dir = output_dir or Path('charts')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style safely
        try:
            plt.style.use(style)
        except OSError:
            # Fallback if style not available
            try:
                plt.style.use('ggplot')
            except OSError:
                pass  # Use default style
        
        # Color scheme - list/tuple collection
        self.colors = [
            '#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f39c12',
            '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b'
        ]
        
        self._charts_created = []  # list to track created charts
    
    def _generate_filename(self, prefix: str, extension: str = 'png') -> Path:
        """
        Generate unique filename for chart.
        
        Demonstrates: f-strings, string formatting
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}.{extension}"
        return self.output_dir / filename
    
    def create_genre_bar_chart(
        self,
        genre_stats: Dict[str, Dict[str, float]],
        metric: str = 'mean'
    ) -> str:
        """
        Create bar chart of genre statistics.
        
        Demonstrates: Matplotlib bar chart, for loop, dict processing,
                     NumPy arrays, f-strings for labels
        """
        if not genre_stats:
            return None
        
        # Extract data using for loop
        genres = []
        values = []
        
        for genre, stats in genre_stats.items():
            genres.append(genre)
            values.append(stats.get(metric, 0))
        
        # Sort by value using lambda
        sorted_pairs = sorted(
            zip(genres, values),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Unzip
        genres, values = zip(*sorted_pairs) if sorted_pairs else ([], [])
        
        # Convert to NumPy array
        values_array = np.array(values)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create bar positions
        x_pos = np.arange(len(genres))
        
        # Create bars with colors
        bars = ax.bar(x_pos, values_array, color=self.colors[:len(genres)])
        
        # Customize chart
        ax.set_xlabel('Genre', fontsize=12)
        ax.set_ylabel(f'{metric.title()} Rating', fontsize=12)  # f-string
        ax.set_title(f'Average Ratings by Genre ({metric.title()})', fontsize=14)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(genres, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, values_array):
            height = bar.get_height()
            ax.annotate(
                f'{value:.2f}',  # f-string with format
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=9
            )
        
        plt.tight_layout()
        
        # Save chart
        filepath = self._generate_filename('genre_bar')
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        self._charts_created.append(str(filepath))
        return str(filepath.relative_to(self.output_dir.parent))
    
    def create_genre_pie_chart(
        self,
        genre_stats: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Create pie chart of genre distribution.
        
        Demonstrates: Matplotlib pie chart, collections, loops
        """
        if not genre_stats:
            return None
        
        # Extract counts
        genres = []
        counts = []
        
        for genre, stats in genre_stats.items():
            genres.append(genre)
            counts.append(stats.get('count', 0))
        
        # Filter out zeros and limit to top 8
        filtered = [
            (g, c) for g, c in zip(genres, counts) if c > 0
        ]
        filtered.sort(key=lambda x: x[1], reverse=True)
        filtered = filtered[:8]
        
        if not filtered:
            return None
        
        genres, counts = zip(*filtered)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie with percentages
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=genres,
            autopct='%1.1f%%',
            colors=self.colors[:len(genres)],
            explode=[0.02] * len(genres),  # list multiplication
            shadow=True,
            startangle=90
        )
        
        ax.set_title('Rating Distribution by Genre', fontsize=14)
        
        # Save
        filepath = self._generate_filename('genre_pie')
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        self._charts_created.append(str(filepath))
        return str(filepath.relative_to(self.output_dir.parent))
    
    def create_rating_histogram(
        self,
        ratings: List[float],
        bins: int = 10
    ) -> str:
        """
        Create histogram of rating distribution.
        
        Demonstrates: Matplotlib histogram, NumPy arrays,
                     statistics overlay
        """
        if not ratings:
            return None
        
        # Convert to NumPy array
        ratings_array = np.array(ratings, dtype=np.float64)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create histogram
        n, bins_edges, patches = ax.hist(
            ratings_array,
            bins=bins,
            color=self.colors[0],
            edgecolor='white',
            alpha=0.7,
            range=(0, 5)
        )
        
        # Calculate statistics for overlay
        mean_val = np.mean(ratings_array)
        median_val = np.median(ratings_array)
        std_val = np.std(ratings_array)
        
        # Add vertical lines for mean and median
        ax.axvline(
            mean_val,
            color=self.colors[2],
            linestyle='--',
            linewidth=2,
            label=f'Mean: {mean_val:.2f}'
        )
        ax.axvline(
            median_val,
            color=self.colors[1],
            linestyle='-.',
            linewidth=2,
            label=f'Median: {median_val:.2f}'
        )
        
        # Customize
        ax.set_xlabel('Rating (Stars)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(f'Rating Distribution (n={len(ratings)}, σ={std_val:.2f})', fontsize=14)
        ax.legend(loc='upper left')
        ax.set_xlim(0, 5.5)
        
        plt.tight_layout()
        
        # Save
        filepath = self._generate_filename('rating_hist')
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        self._charts_created.append(str(filepath))
        return str(filepath.relative_to(self.output_dir.parent))
    
    def create_ratings_timeline(
        self,
        timeline_data: List[Dict[str, Any]]
    ) -> str:
        """
        Create line chart of ratings over time.
        
        Demonstrates: Matplotlib line chart, date handling,
                     for loops, if/else filtering
        """
        if not timeline_data:
            return None
        
        # Filter to entries with data
        filtered_data = [
            entry for entry in timeline_data
            if entry.get('count', 0) > 0
        ]
        
        if len(filtered_data) < 2:
            return None
        
        # Extract dates and values
        dates = []
        counts = []
        averages = []
        
        for entry in filtered_data:
            dates.append(entry['date'])
            counts.append(entry['count'])
            avg = entry.get('average')
            averages.append(avg if avg is not None else 0)
        
        # Convert to arrays
        counts_array = np.array(counts)
        averages_array = np.array(averages)
        x_positions = np.arange(len(dates))
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(14, 6))
        
        # Plot counts (bar)
        ax1.bar(
            x_positions,
            counts_array,
            color=self.colors[0],
            alpha=0.6,
            label='Rating Count'
        )
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Number of Ratings', fontsize=12, color=self.colors[0])
        ax1.tick_params(axis='y', labelcolor=self.colors[0])
        
        # Create second y-axis for averages
        ax2 = ax1.twinx()
        ax2.plot(
            x_positions,
            averages_array,
            color=self.colors[2],
            linewidth=2,
            marker='o',
            markersize=4,
            label='Avg Rating'
        )
        ax2.set_ylabel('Average Rating', fontsize=12, color=self.colors[2])
        ax2.tick_params(axis='y', labelcolor=self.colors[2])
        ax2.set_ylim(0, 5.5)
        
        # X-axis labels (show subset if too many)
        if len(dates) > 20:
            # Show every nth label
            step = len(dates) // 10
            tick_positions = x_positions[::step]
            tick_labels = dates[::step]
        else:
            tick_positions = x_positions
            tick_labels = dates
        
        ax1.set_xticks(tick_positions)
        ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
        
        # Title and legend
        ax1.set_title('Ratings Over Time', fontsize=14)
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        
        # Save
        filepath = self._generate_filename('ratings_timeline')
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        self._charts_created.append(str(filepath))
        return str(filepath.relative_to(self.output_dir.parent))
    
    def create_comparison_chart(
        self,
        data: Dict[str, List[float]],
        title: str = 'Comparison'
    ) -> str:
        """
        Create grouped bar chart for comparisons.
        
        Demonstrates: Grouped bars, NumPy positioning, loops
        """
        if not data:
            return None
        
        categories = list(data.keys())
        
        # Assume all lists have same length
        n_groups = len(data[categories[0]]) if categories else 0
        
        if n_groups == 0:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Bar width and positions
        bar_width = 0.8 / len(categories)
        index = np.arange(n_groups)
        
        # Create bars for each category
        for i, category in enumerate(categories):
            values = np.array(data[category])
            position = index + (i * bar_width)
            ax.bar(
                position,
                values,
                bar_width,
                label=category,
                color=self.colors[i % len(self.colors)]
            )
        
        ax.set_xlabel('Group', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend()
        
        plt.tight_layout()
        
        # Save
        filepath = self._generate_filename('comparison')
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        self._charts_created.append(str(filepath))
        return str(filepath.relative_to(self.output_dir.parent))
    
    def get_created_charts(self) -> List[str]:
        """
        Return list of created chart paths.
        
        Demonstrates: Method returning collection
        """
        return self._charts_created.copy()


class ChartIterator:
    """
    Custom iterator for generating multiple charts.
    
    Demonstrates: Custom iterator with __iter__ and __next__,
                 classes, __init__
    """
    
    def __init__(self, generator: ChartGenerator, chart_configs: List[Dict[str, Any]]):
        """
        Initialize chart iterator.
        
        Demonstrates: __init__ with parameters
        """
        self.generator = generator
        self.configs = chart_configs
        self.index = 0
    
    def __iter__(self) -> Iterator:
        """
        Return iterator (self).
        
        Demonstrates: __iter__ for iterator protocol
        """
        self.index = 0
        return self
    
    def __next__(self) -> str:
        """
        Generate next chart.
        
        Demonstrates: __next__, if/else, method dispatch
        """
        if self.index >= len(self.configs):
            raise StopIteration
        
        config = self.configs[self.index]
        self.index += 1
        
        chart_type = config.get('type', 'bar')
        data = config.get('data', {})
        
        # Dispatch based on chart type
        if chart_type == 'bar':
            return self.generator.create_genre_bar_chart(data)
        elif chart_type == 'pie':
            return self.generator.create_genre_pie_chart(data)
        elif chart_type == 'histogram':
            return self.generator.create_rating_histogram(data)
        elif chart_type == 'line':
            return self.generator.create_ratings_timeline(data)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")
    
    def __len__(self) -> int:
        """
        Return number of charts to generate.
        
        Demonstrates: __len__ dunder method
        """
        return len(self.configs)


# ==============================================================
# Utility Functions
# ==============================================================

def create_quick_bar_chart(
    labels: List[str],
    values: List[float],
    title: str,
    output_path: Path
) -> str:
    """
    Quick utility function to create a bar chart.
    
    Demonstrates: Function with type hints, Matplotlib basics
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(len(labels))
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))
    
    ax.bar(x_pos, values, color=colors)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_title(title)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)
    
    return str(output_path)
