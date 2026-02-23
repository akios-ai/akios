# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Cost Tracking and Budget Visualization

Provides comprehensive cost tracking, budget monitoring, and spending analytics
for AKIOS workflows with visual progress bars and status indicators.

Features:
- Budget utilization calculation and color coding
- Per-agent cost breakdown
- Status icons (✅ Healthy, ⚠️ Caution, 🔴 Critical)
- CSV export for cost history
- Trend analysis (7-day spending)
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
from ..ui.rich_output import get_theme_color


def calculate_budget_percentage(spent: float, budget: float) -> float:
    """
    Calculate percentage of budget spent.
    
    Args:
        spent: Amount spent in USD
        budget: Total budget in USD
    
    Returns:
        Percentage spent (0-100+), or 0.0 if budget is zero
    
    Example:
        >>> calculate_budget_percentage(0.50, 1.00)
        50.0
        >>> calculate_budget_percentage(1.50, 1.00)
        150.0
        >>> calculate_budget_percentage(0.0, 0.0)
        0.0
    """
    # SECURITY: Avoid division by zero
    if budget <= 0:
        return 0.0 if spent <= 0 else 100.0
    
    percentage = (spent / budget) * 100.0
    return round(percentage, 2)


def get_cost_color(percentage: float) -> str:
    """
    Get color for budget visualization based on percentage spent.
    
    Color scheme (accessible/colorblind-safe):
    - success: <50% (healthy)
    - warning: 50-80% (caution)
    - error: >80% (critical)
    
    Args:
        percentage: Percentage of budget spent (0-100+)
    
    Returns:
        Semantic color token for Rich styling
    
    Example:
        >>> get_cost_color(25.0)
        '#00ff00'  # success
        >>> get_cost_color(65.0)
        '#ffff00'  # warning
        >>> get_cost_color(90.0)
        '#ff0000'  # error
    """
    if percentage < 50.0:
        return get_theme_color('success')
    elif percentage < 80.0:
        return get_theme_color('warning')
    else:
        return get_theme_color('error')


def get_cost_status_icon(percentage: float) -> str:
    """
    Get status icon for budget health.
    
    Args:
        percentage: Percentage of budget spent (0-100+)
    
    Returns:
        Status emoji/icon
    
    Example:
        >>> get_cost_status_icon(25.0)
        '✅'
        >>> get_cost_status_icon(65.0)
        '⚠️'
        >>> get_cost_status_icon(90.0)
        '🔴'
    """
    if percentage < 50.0:
        return '✅'  # Healthy
    elif percentage < 80.0:
        return '⚠️'  # Caution
    else:
        return '🔴'  # Critical


def get_budget_status(spent: float, budget: float) -> Dict[str, Any]:
    """
    Get comprehensive budget status with all visualization data.
    
    Args:
        spent: Amount spent in USD
        budget: Total budget in USD
    
    Returns:
        Dictionary with:
        - spent (float): Amount spent
        - budget (float): Total budget
        - remaining (float): Budget remaining
        - percentage (float): Percentage spent
        - color (str): Color for visualization
        - status_icon (str): Status emoji
        - status_text (str): Human-readable status
        - is_over_budget (bool): Whether budget exceeded
        - warning_threshold_reached (bool): Whether 80% threshold reached
    
    Example:
        >>> status = get_budget_status(0.60, 1.00)
        >>> status['percentage']
        60.0
        >>> status['color']
        'yellow'
        >>> status['status_icon']
        '⚠️'
    """
    percentage = calculate_budget_percentage(spent, budget)
    color = get_cost_color(percentage)
    status_icon = get_cost_status_icon(percentage)
    
    # Calculate remaining (can be negative if over budget)
    remaining = budget - spent
    is_over_budget = spent > budget
    
    # Determine status text
    if percentage < 50.0:
        status_text = "Healthy"
    elif percentage < 80.0:
        status_text = "Caution"
    elif percentage < 100.0:
        status_text = "Critical"
    else:
        status_text = "Over Budget"
    
    return {
        'spent': round(spent, 4),
        'budget': round(budget, 4),
        'remaining': round(remaining, 4),
        'percentage': percentage,
        'color': color,
        'status_icon': status_icon,
        'status_text': status_text,
        'is_over_budget': is_over_budget,
        'warning_threshold_reached': percentage >= 80.0,
    }


def format_cost_breakdown(workflow_runs: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Format per-agent/workflow cost breakdown for table display.
    
    Args:
        workflow_runs: Dictionary of workflow run data with cost information
    
    Returns:
        List of dictionaries suitable for table rendering, sorted by cost (desc)
    
    Example:
        >>> runs = {
        ...     'workflow1': {'cost': 0.50, 'runs': 3, 'tokens': 1500},
        ...     'workflow2': {'cost': 0.30, 'runs': 1, 'tokens': 800}
        ... }
        >>> breakdown = format_cost_breakdown(runs)
        >>> breakdown[0]['workflow']
        'workflow1'
        >>> breakdown[0]['cost']
        '$0.50'
    """
    breakdown = []
    
    for workflow_id, info in workflow_runs.items():
        cost = info.get('cost', 0.0)
        runs = info.get('runs', 0)
        tokens = info.get('tokens', 0)
        
        breakdown.append({
            'workflow': workflow_id,
            'runs': str(runs),
            'tokens': f"{tokens:,}",  # Thousands separator
            'cost': f"${cost:.4f}",
            'avg_cost': f"${(cost / runs if runs > 0 else 0.0):.4f}",
        })
    
    # Sort by cost (descending)
    breakdown.sort(key=lambda x: float(x['cost'].replace('$', '')), reverse=True)
    
    return breakdown


def calculate_7day_trend(audit_events: List[Any]) -> Dict[str, Any]:
    """
    Calculate 7-day spending trend from audit events.
    
    Args:
        audit_events: List of audit events with timestamp and cost data
    
    Returns:
        Dictionary with:
        - daily_costs (list): Cost per day for last 7 days
        - total_7day (float): Total spending in last 7 days
        - avg_daily (float): Average daily spending
        - trend_direction (str): 'up', 'down', or 'stable'
    
    Example:
        >>> events = [...]  # Mock events
        >>> trend = calculate_7day_trend(events)
        >>> trend['total_7day']
        2.45
    """
    now = datetime.now(tz=timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    
    # Initialize daily costs (last 7 days)
    daily_costs = [0.0] * 7
    
    # Process events
    for event in audit_events:
        timestamp = getattr(event, 'timestamp', None)
        if not timestamp:
            continue
        
        # Convert to datetime if needed
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue
        
        # Ensure timezone-aware for comparison
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Skip events older than 7 days
        if timestamp < seven_days_ago:
            continue
        
        # Calculate day index (0 = today, 6 = 7 days ago)
        days_ago = (now - timestamp).days
        if 0 <= days_ago < 7:
            metadata = getattr(event, 'metadata', {}) or {}
            cost = metadata.get('cost_incurred', 0.0)
            daily_costs[6 - days_ago] += cost  # Reverse index so oldest is first
    
    total_7day = sum(daily_costs)
    avg_daily = total_7day / 7.0 if daily_costs else 0.0
    
    # Determine trend direction (compare first half vs second half)
    first_half_avg = sum(daily_costs[:3]) / 3.0 if daily_costs[:3] else 0.0
    second_half_avg = sum(daily_costs[3:]) / 3.0 if daily_costs[3:] else 0.0
    
    if second_half_avg > first_half_avg * 1.1:  # 10% threshold
        trend_direction = 'up'
    elif second_half_avg < first_half_avg * 0.9:
        trend_direction = 'down'
    else:
        trend_direction = 'stable'
    
    return {
        'daily_costs': [round(c, 4) for c in daily_costs],
        'total_7day': round(total_7day, 4),
        'avg_daily': round(avg_daily, 4),
        'trend_direction': trend_direction,
    }


def export_cost_history_csv(workflow_runs: Dict[str, Dict], output_path: str) -> bool:
    """
    Export cost history to CSV file.
    
    Args:
        workflow_runs: Dictionary of workflow run data
        output_path: Path to output CSV file
    
    Returns:
        True if successful, False otherwise
    
    Format:
        workflow_id,runs,tokens,cost,avg_cost_per_run,last_run
    
    Example:
        >>> runs = {'workflow1': {'cost': 0.50, 'runs': 3, 'tokens': 1500}}
        >>> export_cost_history_csv(runs, 'costs.csv')
        True
    """
    try:
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['workflow_id', 'runs', 'tokens', 'cost', 'avg_cost_per_run', 'last_run']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for workflow_id, info in workflow_runs.items():
                cost = info.get('cost', 0.0)
                runs = info.get('runs', 0)
                tokens = info.get('tokens', 0)
                last_run = info.get('last_run', 'N/A')
                avg_cost = cost / runs if runs > 0 else 0.0
                
                writer.writerow({
                    'workflow_id': workflow_id,
                    'runs': runs,
                    'tokens': tokens,
                    'cost': f"{cost:.4f}",
                    'avg_cost_per_run': f"{avg_cost:.4f}",
                    'last_run': str(last_run) if last_run else 'N/A',
                })
        
        return True
    except (IOError, OSError, PermissionError) as e:
        # Return False on file write errors
        return False
