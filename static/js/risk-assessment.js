// Risk Assessment JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const riskSlider = document.getElementById('risk_level');
    const riskDescription = document.getElementById('risk-description');
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
    
    // Update risk description when slider changes
    riskSlider.addEventListener('input', function() {
        const level = parseInt(this.value);
        riskDescription.textContent = riskDescriptions[level];
    });
    
    // Handle form submission
    riskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitButton = this.querySelector('.submit-button');
        
        // Show loading state
        submitButton.textContent = 'Calculating Portfolio...';
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
            displayPortfolioResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error calculating portfolio. Please try again.');
        } finally {
            // Reset button
            submitButton.textContent = 'Generate My Portfolio';
            submitButton.disabled = false;
        }
    });
    
    function displayPortfolioResults(data) {
        // Update summary stats
        document.getElementById('expected-return').textContent = data.expected_return + '%';
        document.getElementById('volatility').textContent = data.volatility + '%';
        document.getElementById('sharpe-ratio').textContent = (data.expected_return / data.volatility).toFixed(2);
        
        // Create portfolio chart
        createPortfolioChart(data.portfolio);
        
        // Create portfolio details table
        createPortfolioDetails(data.portfolio, data.investment_amount);
        
        // Show results
        portfolioResults.classList.remove('hidden');
        portfolioResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    function createPortfolioChart(portfolio) {
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.portfolioChart) {
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
        background: white;
    }
    
    .allocation-row:nth-child(even) {
        background: var(--background-color);
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
`;
document.head.appendChild(style);