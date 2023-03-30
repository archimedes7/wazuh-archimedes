#ifndef _METRICS_MANAGER_H
#define _METRICS_MANAGER_H

#include <memory>
#include <mutex>
#include <unordered_map>

#include <utils/baseMacros.hpp>

#include <metrics/iMetricsManager.hpp>
#include <metrics/iMetricsManagerAPI.hpp>
#include <metrics/dataHub.hpp>
#include <metrics/metricsScope.hpp>

namespace metrics_manager
{

class MetricsManager : public IMetricsManager, public IMetricsManagerAPI
{
public:
    MetricsManager();
    /**
     * @copydoc IMetricsManager::getMetricsScope
    */

    std::shared_ptr<IMetricsScope> getMetricsScope(const std::string& name, bool delta = false, int exporterIntervalMS = 1000, int exporterTimeoutMS = 300) override;
    
    /**
     * @copydoc IMetricsManager::getScopeNames
    */
    std::vector<std::string> getScopeNames() override;

    /**
     * @copydoc IMetricsManager::start
    */
    void start() override;

    /** 
     * @copydoc IMetricsManager::isRunning
    */
    bool isRunning() override;

    /**
     * @copydoc IMetricsManager::getAllMetrics
    */
    json::Json getAllMetrics() override;

    // API Commands
    std::variant<std::string, base::Error> dumpCmd() override;

    /**
     * @copydoc iMetricsManagerAPI::enableCmd
    */
    void enableCmd(const std::string& scopeName, const std::string& instrumentName, bool newStatus) override;

    /**
     * @copydoc iMetricsManagerAPI::testCmd
    */
    void testCmd() override;

private:

    /**
     * @brief Get the Metrics Scope object
     * 
     * @param metricsScopeName 
     * @return std::shared_ptr<MetricsScope> 
     */
    std::shared_ptr<MetricsScope> getScope(const std::string& metricsScopeName);
private:

    /// @brief Instrumentation scopes across the application.
    std::map<std::string, std::shared_ptr<MetricsScope>> m_mapScopes;

    bool m_statusRunning;

    std::mutex m_mutexScopes;

    std::shared_ptr<metrics_manager::IMetricsScope>  m_scopeMetrics;
};

} // namespace metrics_manager

#endif // _METRICS_MANAGER_H
