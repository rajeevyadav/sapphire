import itertools

import tables
from pylab import *
from scipy.stats import scoreatpercentile, chisquare
from scipy.optimize import curve_fit

from sapphire import clusters
from sapphire.analysis.direction_reconstruction import DirectionReconstruction
from sapphire.simulations.ldf import KascadeLdf
import utils

import artist
import artist.utils


STATION_TIMING_ERR = 2.4
CLUSTER_TIMING_ERR = 5.5


USE_TEX = False

# For matplotlib plots
if USE_TEX:
    rcParams['font.serif'] = 'Computer Modern'
    rcParams['font.sans-serif'] = 'Computer Modern'
    rcParams['font.family'] = 'sans-serif'
    rcParams['figure.figsize'] = [4 * x for x in (1, 2. / 3)]
    rcParams['figure.subplot.left'] = 0.175
    rcParams['figure.subplot.bottom'] = 0.175
    rcParams['font.size'] = 10
    rcParams['legend.fontsize'] = 'small'
    rcParams['text.usetex'] = True


def main(data):
    #plot_sciencepark_cluster()
    #plot_all_single_and_cluster_combinations(data)
    #hist_phi_single_stations(data)
    #hist_theta_single_stations(data)
    #plot_N_vs_R(data)
    #plot_fav_single_vs_cluster(data)
    #plot_fav_single_vs_single(data)
    #plot_fav_uncertainty_single_vs_cluster(data)
    #plot_fav_uncertainty_single_vs_single(data)
    hist_fav_single_stations(data)

def plot_sciencepark_cluster():
    cluster = clusters.ScienceParkCluster(range(501, 507))

    figure()
    xl, yl = [], []
    for station in cluster.stations:
        for detector in station.detectors:
            x, y = detector.get_xy_coordinates()
            xl.append(x)
            yl.append(y)
            scatter(x, y, c='black', s=3)
    axis('equal')

    cluster = clusters.ScienceParkCluster([501, 503, 506])
    pos = []
    for station in cluster.stations:
        x, y, alpha = station.get_xyalpha_coordinates()
        pos.append((x, y))
    for (x0, y0), (x1, y1) in itertools.combinations(pos, 2):
        plot([x0, x1], [y0, y1], 'gray')

    utils.savedata([xl, yl])
    utils.saveplot()

def plot_all_single_and_cluster_combinations(data):
    for station_group in itertools.combinations(range(501, 507), 3):
        for station in station_group:
            plot_direction_single_vs_cluster(data, station, station_group)

def calc_direction_single_vs_cluster(data, station, cluster, limit=None):
    reconstructions = data.root.reconstructions.reconstructions

    station_query = '(N == 1) & s%d & (min_n134 >= 2.)' % station
    cluster_query = '(N == 3) & ' + ' & '.join(['s%d' % u for u in cluster])
    cluster_str = [str(u) for u in cluster]

    sel_station = reconstructions.readWhere(station_query)
    sel_cluster = reconstructions.readWhere(cluster_query)

    theta_cluster, theta_station = [], []
    phi_cluster, phi_station = [], []
    for event_cluster in sel_cluster:
        coinc_id = event_cluster['coinc_id']
        event_station = sel_station.compress(sel_station[:]['coinc_id'] == coinc_id)
        assert len(event_station) <= 1
        if event_station:
            theta_cluster.append(event_cluster['reconstructed_theta'])
            phi_cluster.append(event_cluster['reconstructed_phi'])
            theta_station.append(event_station['reconstructed_theta'])
            phi_station.append(event_station['reconstructed_phi'])

        if limit and len(theta_cluster) >= limit:
            break

    return array(theta_station).flatten(), array(phi_station).flatten(), \
        array(theta_cluster).flatten(), array(phi_cluster).flatten()

def calc_direction_single_vs_single(data, station1, station2):
    reconstructions = data.root.reconstructions.reconstructions

    station1_query = '(N == 1) & s%d & (min_n134 >= 2.)' % station1
    station2_query = '(N == 1) & s%d & (min_n134 >= 2.)' % station2

    sel_station1 = reconstructions.readWhere(station1_query)
    sel_station2 = reconstructions.readWhere(station2_query)

    theta_station2, theta_station1 = [], []
    phi_station2, phi_station1 = [], []
    for event_station2 in sel_station2:
        coinc_id = event_station2['coinc_id']
        event_station1 = sel_station1.compress(sel_station1[:]['coinc_id'] == coinc_id)
        assert len(event_station1) <= 1
        if event_station1:
            theta_station2.append(event_station2['reconstructed_theta'])
            phi_station2.append(event_station2['reconstructed_phi'])
            theta_station1.append(event_station1['reconstructed_theta'])
            phi_station1.append(event_station1['reconstructed_phi'])

    return array(theta_station1).flatten(), array(phi_station1).flatten(), \
        array(theta_station2).flatten(), array(phi_station2).flatten()

def plot_direction_single_vs_cluster(data, station, cluster):
    cluster_str = [str(u) for u in cluster]

    theta_station, phi_station, theta_cluster, phi_cluster = \
        calc_direction_single_vs_cluster(data, station, cluster)

    figsize = list(rcParams['figure.figsize'])
    figsize[1] = figsize[0] / 2
    figure(figsize=figsize)
    subplot(121)
    plot(theta_station, theta_cluster, ',')
    xlabel(r"$\theta_{%d}$" % station)
    ylabel(r"$\theta_{\{%s\}}$" % ','.join(cluster_str))
    xlim(0, pi / 2)
    ylim(0, pi / 2)

    subplot(122)
    plot(phi_station, phi_cluster, ',')
    xlabel(r"$\phi_{%d}$" % station)
    ylabel(r"$\phi_{\{%s\}}$" % ','.join(cluster_str))
    xlim(-pi, pi)
    ylim(-pi, pi)

    utils.saveplot('%d-%s' % (station, '_'.join(cluster_str)))

def hist_phi_single_stations(data):
    reconstructions = data.root.reconstructions.reconstructions

    figure()
    for n, station in enumerate(range(501, 507), 1):
        subplot(2, 3, n)
        query = '(N == 1) & s%d' % station
        phi = reconstructions.readWhere(query, field='reconstructed_phi')
        hist(rad2deg(phi), bins=linspace(-180, 180, 21), histtype='step')
        xlabel(r"$\phi$")
        legend([station])
        locator_params(tight=True, nbins=4)

    utils.saveplot()

def hist_theta_single_stations(data):
    reconstructions = data.root.reconstructions.reconstructions

    figure()
    for n, station in enumerate(range(501, 507), 1):
        subplot(2, 3, n)
        query = '(N == 1) & s%d' % station
        theta = reconstructions.readWhere(query, field='reconstructed_theta')
        hist(rad2deg(theta), bins=linspace(0, 45, 21), histtype='step')
        xlabel(r"$\theta$")
        legend([station])
        locator_params(tight=True, nbins=4)

    utils.saveplot()

def plot_N_vs_R(data):
    stations = range(501, 507)
    station_ids = range(6)
    cluster = clusters.ScienceParkCluster(stations)

    c_index = data.root.coincidences.c_index
    observables = data.root.coincidences.observables

    figure()
    #clf()
    global c_x, c_y
    if 'c_x' in globals():
        scatter(c_x, c_y)
    else:
        stations_in_coincidence = []
        for coincidence_events in c_index:
            stations = [observables[u]['station_id'] for u in
                        coincidence_events]
            stations_in_coincidence.append(stations)

        c_x = []
        c_y = []
        for station1, station2 in itertools.combinations(station_ids, 2):
            condition = [station1 in u and station2 in u for u in
                         stations_in_coincidence]
            N = sum(condition)
            R, phi = cluster.calc_r_and_phi_for_stations(station1, station2)
            scatter(R, N)
            c_x.append(R)
            c_y.append(N)

    ldf = KascadeLdf()
    R = linspace(100, 500)
    E = linspace(1e14, 1e19, 100)
    F = E ** -2.7
    N = []
    for r in R:
        x = []
        for f, e in zip(F, E):
            Ne = e / 1e15 * 10 ** 4.8
            density = ldf.get_ldf_value_for_size(r, Ne)
            prob = 1 - exp(-.5 * density)
            x.append(f * prob)
        N.append(mean(x))
    N = array(N)
    f = lambda x, S: S * interp(x, R, N)
    c_x = array(c_x)
    c_y = array(c_y)
    # WTF wrong with point at slightly less than 100 m? 501 / 502??
    sc_x = c_x.compress(c_x >= 100)
    sc_y = c_y.compress(c_x >= 100)
    popt, pcov = curve_fit(f, sc_x, sc_y, p0=(1e45))
    plot(R, f(R, popt[0]))
    #ylim(0, 150000)
    ylim(0, 500000)
    xlim(0, 500)
            
    xlabel("Distance [m]")
    ylabel("Number of coincidences")

    utils.saveplot()

def plot_fav_single_vs_cluster(data):
    cluster = [501, 503, 506]
    cluster_str = [str(u) for u in cluster]

    figure()
    for n, station in enumerate(cluster, 1):
        theta_station, phi_station, theta_cluster, phi_cluster = \
            calc_direction_single_vs_cluster(data, station, cluster, 2000)

        subplot(2, 3, n)
        plot(rad2deg(phi_station), rad2deg(phi_cluster), ',')
        xlabel(r"$\phi_{%d}$" % station)
        xlim(-180, 180)
        ylim(-180, 180)
        locator_params(tight=True, nbins=4)
        if n == 1:
            ylabel(r"$\phi_{\{%s\}}$" % ','.join(cluster_str))

        subplot(2, 3, n + 3)
        plot(rad2deg(theta_station), rad2deg(theta_cluster), ',')
        xlabel(r"$\theta_{%d}$" % station)
        xlim(0, 45)
        ylim(0, 45)
        locator_params(tight=True, nbins=4)
        if n == 1:
            ylabel(r"$\theta_{\{%s\}}$" % ','.join(cluster_str))
    subplots_adjust(wspace=.4, hspace=.4)
    utils.saveplot()

def plot_fav_single_vs_single(data):
    cluster = [501, 503, 506]
    cluster_str = [str(u) for u in cluster]

    figure()
    for i in range(len(cluster)):
        for j in range(len(cluster)):
            station1 = cluster[i]
            station2 = cluster[j]

            theta_station1, phi_station1, theta_station2, phi_station2 = \
                calc_direction_single_vs_single(data, station1, station2)

            subplot(3, 3, j * 3 + i + 1)
            if i > j:
                plot(rad2deg(phi_station1), rad2deg(phi_station2), ',')
                xlim(-180, 180)
                ylim(-180, 180)
            elif i < j:
                plot(rad2deg(theta_station1), rad2deg(theta_station2), ',')
                xlim(0, 45)
                ylim(0, 45)

            if j == 2:
                xlabel(station1)
            if i == 0:
                ylabel(station2)
            locator_params(tight=True, nbins=4)

            #subplot(3, 3, n + 3)
            #plot(rad2deg(theta_station1), rad2deg(theta_station2), ',')
            #xlabel(r"$\theta_{%d}$" % station1)
            #ylabel(r"$\theta_{\{%s\}}$" % ','.join(station2_str))
            #xlim(0, 45)
            #ylim(0, 45)
            #locator_params(tight=True, nbins=4)
    utils.saveplot()

def plot_fav_uncertainty_single_vs_cluster(data):
    cluster = [501, 503, 506]
    cluster_str = [str(u) for u in cluster]
    cluster_ids = [0, 2, 5]

    figure()
    for n, station in enumerate(cluster, 1):
        theta_station, phi_station, theta_cluster, phi_cluster = \
            calc_direction_single_vs_cluster(data, station, cluster)

        bins = linspace(0, deg2rad(45), 11)
        x, y, y2 = [], [], []
        for low, high in zip(bins[:-1], bins[1:]):
            sel_phi_c = phi_cluster.compress((low <= theta_station) &
                                             (theta_station < high))
            sel_phi_s = phi_station.compress((low <= theta_station) &
                                             (theta_station < high))
            sel_theta_c = theta_cluster.compress((low <= theta_station) &
                                                 (theta_station < high))
            sel_theta_s = theta_station.compress((low <= theta_station) &
                                                 (theta_station < high))
            dphi = sel_phi_s - sel_phi_c
            dtheta = sel_theta_s - sel_theta_c
            # make sure phi, theta are between -pi and pi
            dphi = (dphi + pi) % (2 * pi) - pi
            dtheta = (dtheta + pi) % (2 * pi) - pi
            print rad2deg((low + high) / 2), len(dphi), len(dtheta)
            x.append((low + high) / 2)
            #y.append(std(dphi))
            #y2.append(std(dtheta))
            y.append((scoreatpercentile(dphi, 83) - scoreatpercentile(dphi, 17)) / 2)
            y2.append((scoreatpercentile(dtheta, 83) - scoreatpercentile(dtheta, 17)) / 2)

        ex = linspace(0, deg2rad(45), 50)
        ephi, etheta = [], []
        for theta in ex:
            ephi.append(calc_phi_error_for_station_cluster(theta, n,
                                                           cluster_ids))
            etheta.append(calc_theta_error_for_station_cluster(theta, n,
                                                               cluster_ids))

        subplot(2, 3, n)
        plot(rad2deg(x), rad2deg(y), 'o')
        plot(rad2deg(ex), rad2deg(ephi))
        xlabel(r"$\theta_{%d}$ [deg]" % station)
        if n == 1:
            ylabel(r"$\phi$ uncertainty [deg]")
        ylim(0, 100)
        locator_params(tight=True, nbins=4)

        subplot(2, 3, n + 3)
        plot(rad2deg(x), rad2deg(y2), 'o')
        plot(rad2deg(ex), rad2deg(etheta))
        xlabel(r"$\theta_{%d}$ [deg]" % station)
        if n == 1:
            ylabel(r"$\theta$ uncertainty [deg]")
        #ylabel(r"$\theta_{\{%s\}}$" % ','.join(cluster_str))
        ylim(0, 15)
        locator_params(tight=True, nbins=4)
    subplots_adjust(wspace=.3, hspace=.3)
    utils.saveplot()

def plot_fav_uncertainty_single_vs_single(data):
    cluster = [501, 503, 506]
    cluster_str = [str(u) for u in cluster]

    figure()
    for i in range(len(cluster)):
        for j in range(len(cluster)):
            station1 = cluster[i]
            station2 = cluster[j]

            theta_station1, phi_station1, theta_station2, phi_station2 = \
                calc_direction_single_vs_single(data, station1, station2)

            bins = linspace(0, deg2rad(45), 11)
            x, y, y2 = [], [], []
            for low, high in zip(bins[:-1], bins[1:]):
                sel_phi_c = phi_station2.compress((low <= theta_station1) &
                                                 (theta_station1 < high))
                sel_phi_s = phi_station1.compress((low <= theta_station1) &
                                                 (theta_station1 < high))
                sel_theta_c = theta_station2.compress((low <= theta_station1) &
                                                     (theta_station1 < high))
                sel_theta_s = theta_station1.compress((low <= theta_station1) &
                                                     (theta_station1 < high))
                dphi = sel_phi_s - sel_phi_c
                dtheta = sel_theta_s - sel_theta_c
                # make sure phi, theta are between -pi and pi
                dphi = (dphi + pi) % (2 * pi) - pi
                dtheta = (dtheta + pi) % (2 * pi) - pi
                print rad2deg((low + high) / 2), len(dphi), len(dtheta)
                x.append((low + high) / 2)
                #y.append(std(dphi))
                #y2.append(std(dtheta))
                y.append((scoreatpercentile(dphi, 83) - scoreatpercentile(dphi, 17)) / 2)
                y2.append((scoreatpercentile(dtheta, 83) - scoreatpercentile(dtheta, 17)) / 2)

            ex = linspace(0, deg2rad(45), 50)
            ephi, etheta = [], []
            for theta in ex:
                ephi.append(calc_phi_error_for_station_station(theta, i, j))
                etheta.append(calc_theta_error_for_station_station(theta, i, j))

            subplot(3, 3, j * 3 + i + 1)
            if i > j:
                plot(rad2deg(x), rad2deg(y), 'o')
                plot(rad2deg(ex), rad2deg(ephi))
                ylim(0, 100)
            elif i < j:
                plot(rad2deg(x), rad2deg(y2), 'o')
                plot(rad2deg(ex), rad2deg(etheta))
                ylim(0, 15)

            xlim(0, 45)

            if j == 2:
                xlabel(station1)
            if i == 0:
                ylabel(station2)
            locator_params(tight=True, nbins=4)

    utils.saveplot()

def calc_phi_error_for_station_cluster(theta, station, cluster):
    phis = linspace(-pi, pi, 50)
    rec = DirectionReconstruction
    sciencepark = clusters.ScienceParkCluster(range(501, 507))

    r1, phi1 = sciencepark.stations[station].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station].calc_r_and_phi_for_detectors(1, 4)
    err_single = rec.rel_phi_errorsq(theta, phis, phi1, phi2, r1, r2)

    r1, phi1 = sciencepark.calc_r_and_phi_for_stations(cluster[0], cluster[1])
    r2, phi2 = sciencepark.calc_r_and_phi_for_stations(cluster[0], cluster[2])
    err_cluster = rec.rel_phi_errorsq(theta, phis, phi1, phi2, r1, r2)

    # errors are already squared!!
    err_total = sqrt(STATION_TIMING_ERR ** 2 * err_single +
                     CLUSTER_TIMING_ERR ** 2 * err_cluster)
    return mean(err_total)

def calc_theta_error_for_station_cluster(theta, station, cluster):
    phis = linspace(-pi, pi, 50)
    rec = DirectionReconstruction
    sciencepark = clusters.ScienceParkCluster(range(501, 507))

    r1, phi1 = sciencepark.stations[station].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station].calc_r_and_phi_for_detectors(1, 4)
    err_single = rec.rel_theta1_errorsq(theta, phis, phi1, phi2, r1, r2)

    r1, phi1 = sciencepark.calc_r_and_phi_for_stations(cluster[0], cluster[1])
    r2, phi2 = sciencepark.calc_r_and_phi_for_stations(cluster[0], cluster[2])
    err_cluster = rec.rel_theta1_errorsq(theta, phis, phi1, phi2, r1, r2)

    # errors are already squared!!
    err_total = sqrt(STATION_TIMING_ERR ** 2 * err_single +
                     CLUSTER_TIMING_ERR ** 2 * err_cluster)
    return mean(err_total)

def calc_phi_error_for_station_station(theta, station1, station2):
    phis = linspace(-pi, pi, 50)
    rec = DirectionReconstruction
    sciencepark = clusters.ScienceParkCluster(range(501, 507))

    r1, phi1 = sciencepark.stations[station1].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station1].calc_r_and_phi_for_detectors(1, 4)
    err_single1 = rec.rel_phi_errorsq(theta, phis, phi1, phi2, r1, r2)

    r1, phi1 = sciencepark.stations[station2].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station2].calc_r_and_phi_for_detectors(1, 4)
    err_single2 = rec.rel_phi_errorsq(theta, phis, phi1, phi2, r1, r2)

    # errors are already squared!!
    err_total = sqrt(STATION_TIMING_ERR ** 2 * err_single1 +
                     STATION_TIMING_ERR ** 2 * err_single2)
    return mean(err_total)

def calc_theta_error_for_station_station(theta, station1, station2):
    phis = linspace(-pi, pi, 50)
    rec = DirectionReconstruction
    sciencepark = clusters.ScienceParkCluster(range(501, 507))

    r1, phi1 = sciencepark.stations[station1].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station1].calc_r_and_phi_for_detectors(1, 4)
    err_single1 = rec.rel_theta1_errorsq(theta, phis, phi1, phi2, r1, r2)

    r1, phi1 = sciencepark.stations[station2].calc_r_and_phi_for_detectors(1, 3)
    r2, phi2 = sciencepark.stations[station2].calc_r_and_phi_for_detectors(1, 4)
    err_single2 = rec.rel_theta1_errorsq(theta, phis, phi1, phi2, r1, r2)

    # errors are already squared!!
    err_total = sqrt(STATION_TIMING_ERR ** 2 * err_single1 +
                     STATION_TIMING_ERR ** 2 * err_single2)
    return mean(err_total)

def hist_fav_single_stations(data):
    reconstructions = data.root.reconstructions.reconstructions

    graph1 = artist.MultiPlot(1, 3, width=r'.35\linewidth')
    graph2 = artist.MultiPlot(1, 3, width=r'.35\linewidth')

    figure()
    for n, station in enumerate([501, 503, 506], 1):
        query = '(N == 1) & s%d' % station
        phi = reconstructions.readWhere(query, field='reconstructed_phi')
        theta = reconstructions.readWhere(query, field='reconstructed_theta')

        subplot(2, 3, n)
        N, bins, patches = hist(rad2deg(phi), bins=linspace(-180, 180, 21),
                                histtype='step')
        x = (bins[:-1] + bins[1:]) / 2
        f = lambda x, a: a
        popt, pcov = curve_fit(f, x, N, sigma=sqrt(N))
        chi2 = chisquare(N, popt[0], ddof=0)
        print station, popt, pcov, chi2

        axhline(popt[0])
        xlabel(r"$\phi$")
        legend([station], loc='lower right')
        locator_params(tight=True, nbins=4)
        axis('auto')

        graph1.histogram(0, n - 1, N, bins)
        graph1.set_label(0, n - 1, station)

        subplot(2, 3, n + 3)
        N, bins, patches = hist(rad2deg(theta), bins=linspace(0, 45, 21),
                                histtype='step')
        xlabel(r"$\theta$")
        legend([station], loc='lower right')
        locator_params(tight=True, nbins=4)
        axis('auto')

        graph2.histogram(0, n - 1, N, bins)
        graph2.set_label(0, n - 1, station)

    subplots_adjust(wspace=.4)
    utils.saveplot()

    graph1.set_ylimits(0, 1500)
    graph1.set_xlimits(-180, 180)
    graph1.show_yticklabels(0, 0)
    graph1.show_xticklabels_for_all()
    graph1.set_xticklabels_position(0, 1, 'right')
    graph1.set_xticks(range(-180, 181, 90))
    graph1.set_xlabel(r'$\phi [\si{\degree}]$')
    graph1.set_ylabel('Count')
    artist.utils.save_graph(graph1, suffix='phi', dirname='plots')

    graph2.set_ylimits(0, 2000)
    graph2.set_xlimits(0, 45)
    graph2.show_yticklabels(0, 0)
    graph2.show_xticklabels_for_all()
    graph2.set_xticklabels_position(0, 1, 'right')
    graph2.set_xlabel(r'$\theta [\si{\degree}]$')
    graph2.set_ylabel('Count')
    artist.utils.save_graph(graph2, suffix='theta', dirname='plots')


if __name__ == '__main__':
    if 'data' not in globals():
        data = tables.openFile('month-single.h5')

    artist.utils.set_prefix("SP-DIR-")
    utils.set_prefix("SP-DIR-")
    main(data)
