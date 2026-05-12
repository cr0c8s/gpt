#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/netanim-module.h"
#include "ns3/olsr-helper.h"
#include "ns3/propagation-module.h"

#include <fstream>
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("WifiResearch");

double simTime = 80.0;
uint32_t packetSize = 1024;
std::string offeredRate = "2Mbps";

struct FlowResult
{
    uint32_t flowId;
    std::string src;
    std::string dst;
    uint32_t txPackets;
    uint32_t rxPackets;
    double packetLoss;
    double throughputMbps;
    double delayS;
    double jitterS;
    uint64_t txBytes;
    uint64_t rxBytes;
};

std::vector<FlowResult>
CollectStats(Ptr<FlowMonitor> monitor,
             FlowMonitorHelper& helper,
             std::string name)
{
    monitor->CheckForLostPackets();

    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier>(
            helper.GetClassifier());

    auto stats = monitor->GetFlowStats();
    std::vector<FlowResult> results;

    std::cout << "\n========================================";
    std::cout << "\n  TOPOLOGY: " << name;
    std::cout << "\n========================================\n";

    for (auto const& flow : stats)
    {
        auto t = classifier->FindFlow(flow.first);
        FlowResult r;
        r.flowId = flow.first;
        r.src = std::to_string(t.sourceAddress.Get());
        r.dst = std::to_string(t.destinationAddress.Get());
        r.txPackets = flow.second.txPackets;
        r.rxPackets = flow.second.rxPackets;
        r.txBytes = flow.second.txBytes;
        r.rxBytes = flow.second.rxBytes;

        std::ostringstream srcStr, dstStr;
        t.sourceAddress.Print(srcStr);
        t.destinationAddress.Print(dstStr);
        r.src = srcStr.str();
        r.dst = dstStr.str();

        std::cout << "\n  Flow " << r.flowId
                  << ": " << r.src << " -> " << r.dst << "\n";
        std::cout << "    Tx Packets : " << r.txPackets << "\n";
        std::cout << "    Rx Packets : " << r.rxPackets << "\n";
        std::cout << "    Tx Bytes   : " << r.txBytes << "\n";
        std::cout << "    Rx Bytes   : " << r.rxBytes << "\n";

        if (flow.second.rxPackets == 0)
        {
            r.packetLoss = 100.0;
            r.throughputMbps = 0.0;
            r.delayS = 0.0;
            r.jitterS = 0.0;
            std::cout << "    ** NO PACKETS RECEIVED **\n";
        }
        else
        {
            double duration =
                flow.second.timeLastRxPacket.GetSeconds() -
                flow.second.timeFirstTxPacket.GetSeconds();

            r.throughputMbps = (duration > 0)
                ? flow.second.rxBytes * 8.0 / duration / 1e6
                : 0.0;

            r.delayS =
                flow.second.delaySum.GetSeconds() /
                flow.second.rxPackets;

            r.jitterS =
                flow.second.jitterSum.GetSeconds() /
                flow.second.rxPackets;

            r.packetLoss =
                (r.txPackets > 0)
                ? ((r.txPackets - r.rxPackets) * 100.0 / r.txPackets)
                : 0.0;

            std::cout << std::fixed << std::setprecision(4);
            std::cout << "    Packet Loss  : " << r.packetLoss << " %\n";
            std::cout << "    Throughput   : " << r.throughputMbps << " Mbps\n";
            std::cout << "    Avg Delay    : " << r.delayS * 1000.0 << " ms\n";
            std::cout << "    Avg Jitter   : " << r.jitterS * 1000.0 << " ms\n";
        }

        results.push_back(r);
    }

    return results;
}

void WriteCSV(const std::string& filename,
              const std::string& topology,
              const std::vector<FlowResult>& results)
{
    std::ofstream f(filename);
    f << "topology,flow_id,src,dst,tx_packets,rx_packets,"
      << "tx_bytes,rx_bytes,packet_loss_pct,throughput_mbps,"
      << "avg_delay_ms,avg_jitter_ms\n";

    for (auto& r : results)
    {
        f << topology << ","
          << r.flowId << ","
          << r.src << ","
          << r.dst << ","
          << r.txPackets << ","
          << r.rxPackets << ","
          << r.txBytes << ","
          << r.rxBytes << ","
          << std::fixed << std::setprecision(6)
          << r.packetLoss << ","
          << r.throughputMbps << ","
          << r.delayS * 1000.0 << ","
          << r.jitterS * 1000.0 << "\n";
    }
    f.close();
}

void SetupWifi(WifiHelper& wifi,
               WifiMacHelper& mac,
               YansWifiPhyHelper& phy,
               Ptr<YansWifiChannel> channel)
{
    wifi.SetStandard(WIFI_STANDARD_80211n);

    wifi.SetRemoteStationManager(
        "ns3::ConstantRateWifiManager",
        "DataMode",
        StringValue("HtMcs3"),
        "ControlMode",
        StringValue("HtMcs0"));

    mac.SetType("ns3::AdhocWifiMac");

    phy.SetChannel(channel);

    phy.Set("TxPowerStart", DoubleValue(20));
    phy.Set("TxPowerEnd", DoubleValue(20));
}

Ptr<YansWifiChannel>
CreateChannel(double range)
{
    YansWifiChannelHelper channelHelper;

    channelHelper.SetPropagationDelay(
        "ns3::ConstantSpeedPropagationDelayModel");

    channelHelper.AddPropagationLoss(
        "ns3::RangePropagationLossModel",
        "MaxRange",
        DoubleValue(range));

    return channelHelper.Create();
}

void RunChain()
{
    NodeContainer nodes;
    nodes.Create(12);

    WifiHelper wifi;
    WifiMacHelper mac;
    YansWifiPhyHelper phy;

    Ptr<YansWifiChannel> channel =
        CreateChannel(18.0);

    SetupWifi(wifi, mac, phy, channel);

    NetDeviceContainer devices =
        wifi.Install(phy, mac, nodes);

    MobilityHelper mobility;

    Ptr<ListPositionAllocator> pos =
        CreateObject<ListPositionAllocator>();

    for (int i = 0; i < 12; ++i)
    {
        pos->Add(Vector(i * 10.0, 0, 0));
    }

    mobility.SetPositionAllocator(pos);
    mobility.SetMobilityModel(
        "ns3::ConstantPositionMobilityModel");
    mobility.Install(nodes);

    OlsrHelper olsr;
    InternetStackHelper internet;
    internet.SetRoutingHelper(olsr);
    internet.Install(nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase("10.1.0.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces =
        ipv4.Assign(devices);

    uint16_t port = 5000;

    PacketSinkHelper sinkHelper(
        "ns3::UdpSocketFactory",
        InetSocketAddress(Ipv4Address::GetAny(), port));

    auto sink = sinkHelper.Install(nodes.Get(11));
    sink.Start(Seconds(1.0));
    sink.Stop(Seconds(simTime));

    OnOffHelper onoff(
        "ns3::UdpSocketFactory",
        InetSocketAddress(interfaces.GetAddress(11), port));

    onoff.SetConstantRate(
        DataRate(offeredRate), packetSize);

    auto app = onoff.Install(nodes.Get(0));
    app.Start(Seconds(20.0));
    app.Stop(Seconds(simTime - 1));

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> monitor = flowHelper.InstallAll();

    AnimationInterface anim("chain.xml");
    for (uint32_t i = 0; i < nodes.GetN(); ++i)
    {
        anim.UpdateNodeDescription(
            nodes.Get(i),
            "N" + std::to_string(i + 1));
        anim.UpdateNodeColor(nodes.Get(i), 0, 200, 0);
    }
    anim.UpdateNodeColor(nodes.Get(0), 255, 100, 0);
    anim.UpdateNodeColor(nodes.Get(11), 255, 0, 0);

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    auto results = CollectStats(monitor, flowHelper, "CHAIN (sequential)");
    WriteCSV("chain-results.csv", "chain", results);

    monitor->SerializeToXmlFile("chain-results.xml", true, true);

    Simulator::Destroy();
}

void RunCluster()
{
    NodeContainer masters;
    masters.Create(3);

    NodeContainer slaves1;
    slaves1.Create(3);

    NodeContainer slaves2;
    slaves2.Create(3);

    NodeContainer slaves3;
    slaves3.Create(3);

    NodeContainer all;
    all.Add(masters);
    all.Add(slaves1);
    all.Add(slaves2);
    all.Add(slaves3);

    Ptr<YansWifiChannel> ch1 = CreateChannel(25.0);
    Ptr<YansWifiChannel> ch2 = CreateChannel(25.0);
    Ptr<YansWifiChannel> ch3 = CreateChannel(25.0);
    Ptr<YansWifiChannel> backboneCh = CreateChannel(80.0);

    WifiHelper wifi1, wifi2, wifi3, wifiBackbone;
    WifiMacHelper mac1, mac2, mac3, macBackbone;
    YansWifiPhyHelper phy1, phy2, phy3, phyBackbone;

    SetupWifi(wifi1, mac1, phy1, ch1);
    SetupWifi(wifi2, mac2, phy2, ch2);
    SetupWifi(wifi3, mac3, phy3, ch3);
    SetupWifi(wifiBackbone, macBackbone, phyBackbone, backboneCh);

    NodeContainer cluster1;
    cluster1.Add(masters.Get(0));
    cluster1.Add(slaves1);

    NodeContainer cluster2;
    cluster2.Add(masters.Get(1));
    cluster2.Add(slaves2);

    NodeContainer cluster3;
    cluster3.Add(masters.Get(2));
    cluster3.Add(slaves3);

    auto dev1 = wifi1.Install(phy1, mac1, cluster1);
    auto dev2 = wifi2.Install(phy2, mac2, cluster2);
    auto dev3 = wifi3.Install(phy3, mac3, cluster3);
    auto backbone = wifiBackbone.Install(
        phyBackbone, macBackbone, masters);

    MobilityHelper mobility;

    Ptr<ListPositionAllocator> pos =
        CreateObject<ListPositionAllocator>();

    pos->Add(Vector(0, 0, 0));
    pos->Add(Vector(40, 0, 0));
    pos->Add(Vector(80, 0, 0));

    pos->Add(Vector(-10, 10, 0));
    pos->Add(Vector(-10, -10, 0));
    pos->Add(Vector(-20, 0, 0));

    pos->Add(Vector(30, 10, 0));
    pos->Add(Vector(30, -10, 0));
    pos->Add(Vector(20, 0, 0));

    pos->Add(Vector(90, 10, 0));
    pos->Add(Vector(90, -10, 0));
    pos->Add(Vector(100, 0, 0));

    mobility.SetPositionAllocator(pos);
    mobility.SetMobilityModel(
        "ns3::ConstantPositionMobilityModel");
    mobility.Install(all);

    OlsrHelper olsr;
    InternetStackHelper internet;
    internet.SetRoutingHelper(olsr);
    internet.Install(all);

    Ipv4AddressHelper ipv4;

    ipv4.SetBase("10.1.1.0", "255.255.255.0");
    auto if1 = ipv4.Assign(dev1);

    ipv4.SetBase("10.1.2.0", "255.255.255.0");
    auto if2 = ipv4.Assign(dev2);

    ipv4.SetBase("10.1.3.0", "255.255.255.0");
    auto if3 = ipv4.Assign(dev3);

    ipv4.SetBase("10.1.10.0", "255.255.255.0");
    auto ifBackbone = ipv4.Assign(backbone);

    uint16_t port = 6000;

    PacketSinkHelper sinkHelper(
        "ns3::UdpSocketFactory",
        InetSocketAddress(Ipv4Address::GetAny(), port));

    auto sink = sinkHelper.Install(slaves3.Get(2));
    sink.Start(Seconds(1.0));
    sink.Stop(Seconds(simTime));

    OnOffHelper onoff(
        "ns3::UdpSocketFactory",
        InetSocketAddress(if3.GetAddress(3), port));

    onoff.SetConstantRate(
        DataRate(offeredRate), packetSize);

    auto app = onoff.Install(slaves1.Get(0));
    app.Start(Seconds(20.0));
    app.Stop(Seconds(simTime - 1));

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> monitor = flowHelper.InstallAll();

    AnimationInterface anim("cluster.xml");

    std::string masterNames[] = {"M1", "M2", "M3"};
    for (uint32_t i = 0; i < masters.GetN(); ++i)
    {
        anim.UpdateNodeDescription(masters.Get(i), masterNames[i]);
        anim.UpdateNodeColor(masters.Get(i), 255, 0, 0);
    }

    std::string slaveNames1[] = {"S1.1", "S1.2", "S1.3"};
    std::string slaveNames2[] = {"S2.1", "S2.2", "S2.3"};
    std::string slaveNames3[] = {"S3.1", "S3.2", "S3.3"};

    for (uint32_t i = 0; i < 3; ++i)
    {
        anim.UpdateNodeDescription(slaves1.Get(i), slaveNames1[i]);
        anim.UpdateNodeColor(slaves1.Get(i), 0, 100, 255);

        anim.UpdateNodeDescription(slaves2.Get(i), slaveNames2[i]);
        anim.UpdateNodeColor(slaves2.Get(i), 0, 100, 255);

        anim.UpdateNodeDescription(slaves3.Get(i), slaveNames3[i]);
        anim.UpdateNodeColor(slaves3.Get(i), 0, 100, 255);
    }

    anim.UpdateNodeColor(slaves1.Get(0), 255, 165, 0);
    anim.UpdateNodeColor(slaves3.Get(2), 255, 0, 255);

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    auto results = CollectStats(monitor, flowHelper, "CLUSTER (grouped by frequency)");
    WriteCSV("cluster-results.csv", "cluster", results);

    monitor->SerializeToXmlFile("cluster-results.xml", true, true);

    Simulator::Destroy();
}

int main(int argc, char* argv[])
{
    std::string mode = "both";

    CommandLine cmd;
    cmd.AddValue("mode", "Run mode: chain, cluster, or both", mode);
    cmd.Parse(argc, argv);

    if (mode == "chain" || mode == "both")
    {
        std::cout << "\n╔══════════════════════════════════════╗";
        std::cout << "\n║    RUNNING CHAIN (SEQUENTIAL) MODE   ║";
        std::cout << "\n╚══════════════════════════════════════╝\n";
        RunChain();
    }

    if (mode == "cluster" || mode == "both")
    {
        std::cout << "\n╔══════════════════════════════════════╗";
        std::cout << "\n║   RUNNING CLUSTER (GROUPED) MODE     ║";
        std::cout << "\n╚══════════════════════════════════════╝\n";
        RunCluster();
    }

    return 0;
}
