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
Performance Monitor - Track and optimize AKIOS performance metrics

Monitors startup time, memory usage, and operation performance.
Provides benchmarking tools and optimization recommendations.
"""

import time
import os
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

# Optional psutil import with graceful fallback
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False


class PerformanceMonitor:
    """
    Performance monitoring and optimization tools.

    Tracks key performance metrics and provides optimization recommendations.
    """

    def __init__(self):
        self.metrics = {}
        self._process = None  # Lazy initialization to avoid psutil import errors
        self._fallback_start_time = time.time()

    @property
    def process(self):
        """Lazy initialization of psutil process."""
        if self._process is None and HAS_PSUTIL:
            try:
                self._process = psutil.Process(os.getpid())
            except (AttributeError, psutil.Error):
                self._process = None
        return self._process

    @contextmanager
    def measure_time(self, operation_name: str):
        """
        Context manager to measure operation execution time.

        Args:
            operation_name: Name of the operation being measured
        """
        start_time = time.perf_counter()
        start_memory = None
        if self.process:
            try:
                start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            except (AttributeError, psutil.Error):
                start_memory = 0

        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = None
            if self.process:
                try:
                    end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                except (AttributeError, psutil.Error):
                    end_memory = 0

            duration = end_time - start_time
            memory_delta = (end_memory - start_memory) if (start_memory is not None and end_memory is not None) else 0

            self.metrics[operation_name] = {
                'duration_seconds': duration,
                'memory_delta_mb': memory_delta,
                'start_memory_mb': start_memory or 0,
                'end_memory_mb': end_memory or 0
            }

    def get_startup_time(self) -> float:
        """Get current process startup time approximation."""
        if self.process:
            try:
                return time.time() - self.process.create_time()
            except (AttributeError, psutil.Error):
                pass
        return time.time() - self._fallback_start_time

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        if not self.process:
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percentage': 0,
                'note': 'psutil not available'
            }

        try:
            mem_info = self.process.memory_info()
            return {
                'rss_mb': mem_info.rss / 1024 / 1024,
                'vms_mb': mem_info.vms / 1024 / 1024,
                'percentage': self.process.memory_percent()
            }
        except (AttributeError, psutil.Error):
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percentage': 0,
                'note': 'memory info unavailable'
            }

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        memory_stats = self.get_memory_usage()

        cpu_percent = 0
        if self.process:
            try:
                cpu_percent = self.process.cpu_percent(interval=0.1)
            except (AttributeError, psutil.Error):
                cpu_percent = 0

        report = {
            'process_info': {
                'pid': os.getpid(),
                'uptime_seconds': self.get_startup_time(),
                'cpu_percent': cpu_percent,
                'psutil_available': HAS_PSUTIL
            },
            'memory_usage': memory_stats,
            'operation_metrics': self.metrics.copy(),
            'recommendations': self._generate_recommendations(memory_stats)
        }

        return report

    def _generate_recommendations(self, memory_stats: Dict[str, float]) -> Dict[str, str]:
        """Generate performance optimization recommendations."""
        recommendations = {}

        if memory_stats['rss_mb'] > 50:
            recommendations['memory'] = "High memory usage detected. Consider lazy loading for heavy components."

        if self.get_startup_time() > 2.0:
            recommendations['startup'] = "Slow startup time. Consider lazy imports and caching."

        slow_operations = [
            name for name, metrics in self.metrics.items()
            if metrics['duration_seconds'] > 1.0
        ]
        if slow_operations:
            recommendations['operations'] = f"Slow operations detected: {', '.join(slow_operations)}. Consider caching."

        return recommendations

    def benchmark_operation(self, operation: Callable, name: str, iterations: int = 10) -> Dict[str, float]:
        """
        Benchmark an operation over multiple iterations.

        Args:
            operation: Function to benchmark
            name: Name for the benchmark
            iterations: Number of iterations to run

        Returns:
            Benchmark statistics
        """
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            operation()
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        return {
            f'{name}_avg_seconds': avg_time,
            f'{name}_min_seconds': min_time,
            f'{name}_max_seconds': max_time,
            f'{name}_iterations': iterations
        }


# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


@contextmanager
def measure_performance(operation_name: str):
    """
    Context manager for measuring performance of code blocks.

    Args:
        operation_name: Name of the operation being measured
    """
    monitor = get_performance_monitor()
    with monitor.measure_time(operation_name):
        yield
