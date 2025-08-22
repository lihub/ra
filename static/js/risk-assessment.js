// Risk Assessment JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const riskSlider = document.getElementById('risk_level');
    const riskDescription = document.getElementById('risk-description');
    const durationSlider = document.getElementById('investment_duration');
    const durationValue = document.getElementById('duration-value');
    const durationDescription = document.getElementById('duration-description');
    const riskForm = document.getElementById('risk-form');
    const portfolioResults = document.getElementById('portfolio-results');
    
    // Risk level descriptions
    const riskDescriptions = {
        1: "Very Conservative - Capital preservation is priority, minimal volatility",
        2: "Conservative - Low risk, stable returns with minimal fluctuation", 
        3: "Moderately Conservative - Some growth potential with lower volatility",
        4: "Moderate - Balanced approach between stability and growth",
        5: "Moderate - Balanced approach between growth and stability",
        6: "Moderately Aggressive - Higher growth potential with moderate risk",
        7: "Aggressive - Focused on growth with higher volatility tolerance",
        8: "Very Aggressive - Maximum growth potential, comfortable with high volatility",
        9: "Extremely Aggressive - Seeking highest returns, accepting significant risk",
        10: "Maximum Risk - Speculative investments, potential for large gains/losses"
    };
    
    // Duration descriptions
    const durationDescriptions = {
        1: "Very short-term - Focus on capital preservation with minimal risk",
        2: "Short-term - Conservative approach with stable, liquid investments",
        5: "Medium-term - Balanced strategy allowing moderate growth potential",
        10: "Medium-long term - Growth-oriented with time for market volatility",
        15: "Long-term - Aggressive growth strategy leveraging compound returns",
        20: "Very long-term - Maximum growth potential through equity exposure",
        30: "Ultra long-term - Generational wealth building with high risk tolerance"
    };

    function getDurationDescription(years) {
        if (years <= 2) return durationDescriptions[1];
        if (years <= 4) return durationDescriptions[2];
        if (years <= 7) return durationDescriptions[5];
        if (years <= 12) return durationDescriptions[10];
        if (years <= 18) return durationDescriptions[15];
        if (years <= 25) return durationDescriptions[20];
        return durationDescriptions[30];
    }

    // Update risk description when slider changes
    riskSlider.addEventListener('input', function() {
        const level = parseInt(this.value);
        riskDescription.textContent = riskDescriptions[level];
    });

    // Update duration display when slider changes
    durationSlider.addEventListener('input', function() {
        const years = parseInt(this.value);
        durationValue.textContent = years;
        durationDescription.textContent = getDurationDescription(years);
    });
    
    // Handle form submission
    riskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitButton = this.querySelector('.submit-button');
        
        // Show loading state
        submitButton.textContent = 'Creating Your Quantica Portfolio...';
        submitButton.disabled = true;
        
        try {
            const response = await fetch('/api/calculate-portfolio', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            console.log('Portfolio data received:', data);
            displayPortfolioResults(data);
            
        } catch (error) {
            console.error('Error details:', error);
            console.error('Error stack:', error.stack);
            alert('Error calculating portfolio. Please try again.');
        } finally {
            // Reset button
            submitButton.textContent = 'Create My Quantica Portfolio';
            submitButton.disabled = false;
        }
    });
    
    function displayPortfolioResults(data) {
        // Update summary stats
        document.getElementById('expected-return').textContent = data.expected_return.toFixed(1) + '%';
        document.getElementById('volatility').textContent = data.volatility.toFixed(1) + '%';
        document.getElementById('sharpe-ratio').textContent = data.sharpe_ratio.toFixed(2);
        
        // Create portfolio allocation chart
        createPortfolioChart(data.portfolio);
        
        // Create performance chart
        if (data.performance_history && data.performance_history.timeseries) {
            createPerformanceChart(data.performance_history, data.investment_amount);
        }
        
        // Create portfolio details table
        createPortfolioDetails(data.portfolio, data.investment_amount);
        
        // Show results
        portfolioResults.classList.remove('hidden');
        portfolioResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    function createPortfolioChart(portfolio) {
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.portfolioChart && typeof window.portfolioChart.destroy === 'function') {
            window.portfolioChart.destroy();
        }
        
        const labels = Object.keys(portfolio);
        const data = Object.values(portfolio).map(val => val * 100);
        const colors = [
            '#3b82f6', // Blue
            '#10b981', // Green  
            '#f59e0b', // Yellow
            '#ef4444', // Red
            '#8b5cf6', // Purple
            '#06b6d4', // Cyan
            '#84cc16', // Lime
            '#f97316'  // Orange
        ];
        
        window.portfolioChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    function createPerformanceChart(performanceData, investmentAmount) {
        // Create performance chart container if it doesn't exist
        let perfChartContainer = document.getElementById('performance-chart-container');
        if (!perfChartContainer) {
            perfChartContainer = document.createElement('div');
            perfChartContainer.id = 'performance-chart-container';
            perfChartContainer.innerHTML = `
                <h3>Historical Performance</h3>
                <div style="position: relative; height: 400px; margin: 2rem 0;">
                    <canvas id="performanceChart"></canvas>
                </div>
                <div class="performance-stats">
                    <div class="stat">
                        <h4>Total Return</h4>
                        <span id="total-return">${performanceData.summary.total_return_percent.toFixed(1)}%</span>
                    </div>
                    <div class="stat">
                        <h4>Max Drawdown</h4>
                        <span id="max-drawdown">${performanceData.summary.max_drawdown_percent.toFixed(1)}%</span>
                    </div>
                    <div class="stat">
                        <h4>Final Value</h4>
                        <span id="final-value">$${performanceData.summary.final_value.toLocaleString()}</span>
                    </div>
                </div>
            `;
            
            // Insert after portfolio chart
            const portfolioChartDiv = document.querySelector('.portfolio-chart');
            portfolioChartDiv.parentNode.insertBefore(perfChartContainer, portfolioChartDiv.nextSibling);
        }
        
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.performanceChart && typeof window.performanceChart.destroy === 'function') {
            window.performanceChart.destroy();
        }
        
        // Scale the performance data to the actual investment amount
        const scaleFactor = investmentAmount / performanceData.summary.initial_value;
        const scaledData = performanceData.timeseries.map(point => ({
            x: point.date,
            y: point.value * scaleFactor
        }));
        
        // Add baseline (initial investment)
        const baselineData = performanceData.timeseries.map(point => ({
            x: point.date,
            y: investmentAmount
        }));
        
        window.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Portfolio Value',
                    data: scaledData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.1
                }, {
                    label: 'Initial Investment',
                    data: baselineData,
                    borderColor: '#64748b',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 30, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#8b5cf6',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const pnl = value - investmentAmount;
                                const pnlPercent = (pnl / investmentAmount * 100).toFixed(1);
                                return `${context.dataset.label}: $${value.toLocaleString()} (${pnlPercent > 0 ? '+' : ''}${pnlPercent}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                month: 'MMM yyyy'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a1a1aa'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a1a1aa',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    function createPortfolioDetails(portfolio, investmentAmount) {
        const detailsContainer = document.getElementById('portfolio-details');
        
        let html = '<h3>Portfolio Allocation Details</h3><div class="allocation-table">';
        
        for (const [asset, allocation] of Object.entries(portfolio)) {
            const percentage = (allocation * 100).toFixed(1);
            const amount = (allocation * investmentAmount).toFixed(0);
            
            html += `
                <div class="allocation-row">
                    <div class="asset-name">${asset.replace(/_/g, ' ')}</div>
                    <div class="asset-percentage">${percentage}%</div>
                    <div class="asset-amount">$${Number(amount).toLocaleString()}</div>
                </div>
            `;
        }
        
        html += '</div>';
        detailsContainer.innerHTML = html;
    }
});

// Add CSS for allocation table
const style = document.createElement('style');
style.textContent = `
    .allocation-table {
        margin-top: 1rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }
    
    .allocation-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr;
        padding: 1rem;
        border-bottom: 1px solid var(--border-color);
        background: var(--surface-color);
    }
    
    .allocation-row:nth-child(even) {
        background: var(--surface-elevated);
    }
    
    .allocation-row:last-child {
        border-bottom: none;
    }
    
    .asset-name {
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .asset-percentage {
        text-align: center;
        font-weight: 500;
        color: var(--primary-color);
    }
    
    .asset-amount {
        text-align: right;
        font-weight: 500;
        color: var(--text-primary);
    }
    
    #performance-chart-container {
        background: var(--surface-elevated);
        padding: 2rem;
        border-radius: var(--border-radius-lg);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    #performance-chart-container h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .performance-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 2rem;
    }
    
    .performance-stats .stat {
        text-align: center;
        padding: 1rem;
        background: var(--surface-color);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .performance-stats .stat h4 {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .performance-stats .stat span {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
`;
document.head.appendChild(style);