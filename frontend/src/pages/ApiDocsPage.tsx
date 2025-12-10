import Header from "../components/Header";
import Footer from "../components/Footer";
import AIChatWidget from "../components/AIChatWidget";
import {
    Code,
    Database,
    Key,
    ExternalLink,
    Copy,
    Check,
    Play,
    Loader2,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import { useState } from "react";

const API_BASE_URL = "https://api.openinfra.space";

interface EndpointParam {
    name: string;
    type: string;
    desc: string;
    default?: string;
}

interface Endpoint {
    method: string;
    path: string;
    title: string;
    description: string;
    params?: EndpointParam[];
    testPath?: string;
}

// Open Data Endpoints
const openDataEndpoints: Endpoint[] = [
    {
        method: "GET",
        path: "/api/opendata/",
        title: "Thông tin API",
        description: "Thông tin về API và giấy phép sử dụng dữ liệu",
        testPath: "/api/opendata/",
    },
    {
        method: "GET",
        path: "/api/opendata/assets",
        title: "Danh sách tài sản hạ tầng",
        description:
            "Lấy tất cả tài sản hạ tầng dưới dạng GeoJSON FeatureCollection",
        params: [
            {
                name: "skip",
                type: "integer",
                desc: "Số bản ghi bỏ qua (mặc định: 0)",
                default: "0",
            },
            {
                name: "limit",
                type: "integer",
                desc: "Số bản ghi tối đa (mặc định: 100, tối đa: 1000)",
                default: "5",
            },
            {
                name: "feature_type",
                type: "string",
                desc: "Lọc theo loại tài sản",
            },
            {
                name: "feature_code",
                type: "string",
                desc: "Lọc theo mã tài sản",
            },
        ],
        testPath: "/api/opendata/assets?limit=5",
    },
    {
        method: "GET",
        path: "/api/opendata/assets/{asset_id}",
        title: "Chi tiết tài sản",
        description: "Lấy thông tin chi tiết của tài sản theo ID",
        params: [
            {
                name: "asset_id",
                type: "string",
                desc: "ID tài sản (MongoDB ObjectId)",
            },
        ],
    },
    {
        method: "GET",
        path: "/api/opendata/feature-types",
        title: "Danh sách loại hạ tầng",
        description: "Lấy danh sách các loại hạ tầng có sẵn và số lượng của mỗi loại",
        testPath: "/api/opendata/feature-types",
    },
    {
        method: "GET",
        path: "/api/opendata/license",
        title: "Thông tin giấy phép",
        description: "Thông tin về Open Government Licence v3.0 (OGL)",
        testPath: "/api/opendata/license",
    },
];

// IoT NGSI-LD Endpoints
const iotLinkedDataEndpoints: Endpoint[] = [
    {
        method: "GET",
        path: "/api/v1/ld/context",
        title: "Context NGSI-LD",
        description:
            "Lấy tài liệu context NGSI-LD (chuẩn ETSI cho quản lý thông tin ngữ cảnh)",
        testPath: "/api/v1/ld/context",
    },
    {
        method: "GET",
        path: "/api/v1/ld/sensors",
        title: "Cảm biến IoT (NGSI-LD)",
        description:
            "Liệt kê toàn bộ cảm biến IoT ở định dạng NGSI-LD, kèm thuộc tính và quan hệ",
        params: [
            {
                name: "skip",
                type: "integer",
                desc: "Số bản ghi bỏ qua",
                default: "0",
            },
            {
                name: "limit",
                type: "integer",
                desc: "Số bản ghi tối đa (tối đa: 500)",
                default: "100",
            },
            { name: "asset_id", type: "string", desc: "Lọc theo ID tài sản" },
            {
                name: "sensor_type",
                type: "string",
                desc: "Lọc theo loại: temperature, humidity, pressure, vibration",
            },
            {
                name: "status",
                type: "string",
                desc: "Lọc theo trạng thái: online, offline, maintenance",
            },
        ],
        testPath: "/api/v1/ld/sensors?limit=5",
    },
    {
        method: "GET",
        path: "/api/v1/ld/sensors/{sensor_id}",
        title: "Cảm biến đơn (NGSI-LD)",
        description:
            "Lấy một cảm biến đơn ở định dạng NGSI-LD, kèm thuộc tính và quan hệ. Ví dụ ID: 6931b938c2f7cb7eba01df64",
        params: [
            {
                name: "sensor_id",
                type: "string",
                desc: "ID cảm biến (MongoDB ObjectId). Ví dụ: 6931b938c2f7cb7eba01df64",
            },
        ],
        testPath: "/api/v1/ld/sensors/6931b938c2f7cb7eba01df64",
    },
    {
        method: "GET",
        path: "/api/v1/ld/sensors/{sensor_id}/observations",
        title: "Quan trắc cảm biến (NGSI-LD)",
        description:
            "Lấy dữ liệu quan trắc theo cảm biến ở định dạng NGSI-LD với lọc theo khoảng thời gian. Ví dụ cảm biến: 6931b938c2f7cb7eba01df64",
        params: [
            {
                name: "sensor_id",
                type: "string",
                desc: "Sensor ID. Sample: 6931b938c2f7cb7eba01df64",
            },
            {
                name: "from_time",
                type: "string",
                desc: "Thời gian bắt đầu (ISO 8601, ví dụ: 2024-01-01T00:00:00Z)",
            },
            { name: "to_time", type: "string", desc: "End time (ISO 8601)" },
            {
                name: "limit",
                type: "integer",
                desc: "Số quan trắc tối đa (tối đa: 10000)",
                default: "1000",
            },
        ],
        testPath:
            "/api/v1/ld/sensors/6931b938c2f7cb7eba01df64/observations?from_time=2024-01-01T00:00:00Z&to_time=2025-12-31T23:59:59Z&limit=10",
    },
    {
        method: "GET",
        path: "/api/v1/ld/assets/{asset_id}",
        title: "Tài sản kèm dữ liệu IoT (NGSI-LD)",
        description:
            "Lấy tài sản hạ tầng kèm toàn bộ cảm biến liên quan và quan trắc gần đây ở định dạng NGSI-LD. Ví dụ: 6925b9001b74e89f7dab169a",
        params: [
            {
                name: "asset_id",
                type: "string",
                desc: "Asset ID. Sample: 6925b9001b74e89f7dab169a",
            },
            {
                name: "hours",
                type: "integer",
                desc: "Số giờ dữ liệu lịch sử (tối đa: 168)",
                default: "24",
            },
        ],
        testPath: "/api/v1/ld/assets/6925b9001b74e89f7dab169a?hours=24",
    },
    {
        method: "GET",
        path: "/api/v1/ld/observations",
        title: "Tất cả quan trắc (NGSI-LD)",
        description:
            "Lấy các quan trắc gần đây từ tất cả cảm biến ở định dạng NGSI-LD cho nền tảng đô thị thông minh",
        params: [
            {
                name: "hours",
                type: "integer",
                desc: "Số giờ dữ liệu cần lấy (tối đa: 24)",
                default: "1",
            },
            { name: "asset_id", type: "string", desc: "Filter by asset ID" },
            {
                name: "sensor_type",
                type: "string",
                desc: "Filter by sensor type",
            },
            {
                name: "limit",
                type: "integer",
                desc: "Số quan trắc tối đa (tối đa: 5000)",
                default: "500",
            },
        ],
        testPath: "/api/v1/ld/observations?hours=1&limit=10",
    },
    {
        method: "GET",
        path: "/api/v1/ld/vocab",
        title: "OpenInfra Vocabulary",
        description:
            "Get the OpenInfra vocabulary definition extending NGSI-LD and Schema.org",
        testPath: "/api/v1/ld/vocab",
    },
];

// Combine all endpoints for backward compatibility
const endpoints: Endpoint[] = [...openDataEndpoints];

const codeExamples = {
    curl: `curl -X GET "${API_BASE_URL}/api/opendata/assets?limit=10" \\
  -H "Accept: application/json"`,
    javascript: `// Using fetch API
const response = await fetch('${API_BASE_URL}/api/opendata/assets?limit=10');
const data = await response.json();

// Response is GeoJSON FeatureCollection
console.log(data.features);
console.log('License:', data.license);`,
    python: `import requests

response = requests.get(
    '${API_BASE_URL}/api/opendata/assets',
    params={'limit': 10, 'feature_type': 'Power Station'}
)
data = response.json()

# GeoJSON data
for feature in data['features']:
    print(feature['properties']['feature_type'])
    print(feature['geometry']['coordinates'])`,
};

// NGSI-LD IoT code examples
const jsonLdCodeExamples = {
    curl: `# Get IoT sensors in NGSI-LD format
curl -X GET "${API_BASE_URL}/api/v1/ld/sensors?limit=10" \\
  -H "Accept: application/ld+json"

# Get observations for a specific sensor (NGSI-LD)
curl -X GET "${API_BASE_URL}/api/v1/ld/sensors/{sensor_id}/observations?from_time=2024-01-01T00:00:00Z&to_time=2024-12-31T23:59:59Z" \\
  -H "Accept: application/ld+json"`,
    javascript: `// Fetch IoT sensors in NGSI-LD format (ETSI standard)
const response = await fetch('${API_BASE_URL}/api/v1/ld/sensors?limit=10', {
  headers: { 'Accept': 'application/ld+json' }
});
const sensors = await response.json();

// NGSI-LD format: array of entities
sensors.forEach(sensorEntity => {
  console.log('ID:', sensorEntity.id);  // urn:ngsi-ld:Sensor:xxx
  console.log('Type:', sensorEntity.type);  // Sensor
  console.log('Code:', sensorEntity.sensorCode.value);  // Property
  console.log('Status:', sensorEntity.status.value);
  console.log('Asset:', sensorEntity.refAsset.object);  // Relationship
});`,
    python: `import requests

# Fetch NGSI-LD data
response = requests.get(
    '${API_BASE_URL}/api/v1/ld/sensors',
    params={'limit': 10},
    headers={'Accept': 'application/ld+json'}
)
sensors = response.json()

# NGSI-LD entities with Properties and Relationships
for sensor in sensors:
    sensor_id = sensor['id']  # urn:ngsi-ld:Sensor:xxx
    sensor_code = sensor['sensorCode']['value']  # Property
    sensor_type = sensor['sensorType']['value']
    status = sensor['status']['value']
    asset_ref = sensor['refAsset']['object']  # Relationship
    
    print(f"Sensor {sensor_code}: {sensor_type} - {status}")
    print(f"  Monitors asset: {asset_ref}")`,
};

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button
            onClick={handleCopy}
            className="p-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
            title="Sao chép vào clipboard"
        >
            {copied ? (
                <Check size={16} className="text-green-400" />
            ) : (
                <Copy size={16} className="text-slate-300" />
            )}
        </button>
    );
}

function EndpointCard({ endpoint }: { endpoint: Endpoint }) {
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showResponse, setShowResponse] = useState(false);
    const [assetId, setAssetId] = useState("");

    const handleTest = async () => {
        setIsLoading(true);
        setError(null);
        setResponse(null);
        setShowResponse(true);

        try {
            let testUrl = API_BASE_URL;
            if (endpoint.testPath) {
                testUrl += endpoint.testPath;
            } else if (endpoint.path.includes("{asset_id}") && assetId) {
                testUrl += endpoint.path.replace("{asset_id}", assetId);
                } else {
                setError("Vui lòng nhập asset_id để thử");
                setIsLoading(false);
                return;
            }

            const res = await fetch(testUrl);
            const data = await res.json();
            setResponse(JSON.stringify(data, null, 2));
                } catch (err) {
            setError(err instanceof Error ? err.message : "Đã xảy ra lỗi");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-6">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                    <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-mono font-semibold rounded">
                            {endpoint.method}
                        </span>
                        <code className="text-slate-800 font-mono text-sm">
                            {endpoint.path}
                        </code>
                    </div>
                    {endpoint.testPath && (
                        <button
                            onClick={handleTest}
                            disabled={isLoading}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
                        >
                            {isLoading ? (
                                <Loader2 size={16} className="animate-spin" />
                            ) : (
                                <Play size={16} />
                            )}
                            Test
                        </button>
                    )}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-1">
                    {endpoint.title}
                </h3>
                <p className="text-slate-600">{endpoint.description}</p>

                {endpoint.params && (
                    <div className="mt-4">
                        <h4 className="text-sm font-semibold text-slate-700 mb-2">
                            Tham số:
                        </h4>
                        <div className="bg-slate-50 rounded-lg p-4 overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-left text-slate-500">
                                        <th className="pb-2 pr-4">Tên</th>
                                        <th className="pb-2 pr-4">Loại</th>
                                        <th className="pb-2">Mô tả</th>
                                    </tr>
                                </thead>
                                <tbody className="text-slate-700">
                                    {endpoint.params.map((param) => (
                                        <tr key={param.name}>
                                            <td className="py-1 pr-4 font-mono text-blue-600">
                                                {param.name}
                                            </td>
                                            <td className="py-1 pr-4 text-slate-500">
                                                {param.type}
                                            </td>
                                            <td className="py-1">
                                                {param.desc}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Input for asset_id if needed */}
                {endpoint.path.includes("{asset_id}") && (
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Nhập asset_id để thử:
                        </label>
                        <p className="text-xs text-slate-500 mb-2">
                            Ví dụ:{" "}
                            <code
                                className="bg-slate-100 px-2 py-1 rounded cursor-pointer hover:bg-slate-200 transition-colors"
                                onClick={() =>
                                    setAssetId("6927235efbcca60d69c3bf97")
                                }
                                title="Nhấn để dùng ID mẫu"
                            >
                                6927235efbcca60d69c3bf97
                            </code>
                        </p>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={assetId}
                                onChange={(e) => setAssetId(e.target.value)}
                                placeholder="6927235efbcca60d69c3bf97"
                                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                onClick={handleTest}
                                disabled={isLoading || !assetId}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <Loader2
                                        size={16}
                                        className="animate-spin"
                                    />
                                ) : (
                                    <Play size={16} />
                                )}
                                Thử
                            </button>
                        </div>
                    </div>
                )}

                {/* Response Section */}
                {showResponse && (
                    <div className="mt-4">
                        <button
                            onClick={() => setShowResponse(!showResponse)}
                            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 mb-2"
                        >
                            {showResponse ? (
                                <ChevronUp size={16} />
                            ) : (
                                <ChevronDown size={16} />
                            )}
                            Response
                        </button>
                        <div className="bg-slate-900 rounded-lg overflow-hidden">
                            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700">
                                <span className="text-xs text-slate-400">
                                    {error ? "Lỗi" : "application/json"}
                                </span>
                                {response && <CopyButton text={response} />}
                            </div>
                            <div className="p-4 max-h-96 overflow-auto">
                                {isLoading && (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2
                                            size={24}
                                            className="animate-spin text-blue-400"
                                        />
                                    </div>
                                )}
                                {error && (
                                    <p className="text-red-400 text-sm">
                                        {error}
                                    </p>
                                )}
                                {response && (
                                    <pre className="text-sm text-slate-300 overflow-x-auto">
                                        <code>{response}</code>
                                    </pre>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ApiDocsPage() {
    const [activeTab, setActiveTab] = useState<
        "curl" | "javascript" | "python"
    >("javascript");

    const sidebarItems = [
        { id: "opendata", label: "API Dữ liệu Mở", icon: "📦" },
        { id: "iot", label: "Dữ liệu IoT (NGSI-LD)", icon: "📡" },
        { id: "examples", label: "Ví dụ mã", icon: "💻" },
        { id: "mcp", label: "Máy chủ MCP", icon: "🤖" },
    ];

    const scrollToSection = (id: string) => {
        const el = document.getElementById(id);
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
            <Header />

            {/* Sidebar - fixed on desktop */}
            <aside className="hidden lg:block fixed left-0 top-20 w-56 h-[calc(100vh-5rem)] bg-white border-r border-slate-200 p-4 overflow-y-auto z-40">
                <nav className="space-y-1">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-3">
                        Điều hướng
                    </h3>
                    {sidebarItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => scrollToSection(item.id)}
                            className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 hover:text-blue-600 rounded-lg transition-colors text-left"
                        >
                            <span>{item.icon}</span>
                            <span>{item.label}</span>
                        </button>
                    ))}
                </nav>

                {/* <div className="mt-6 pt-6 border-t border-slate-200">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-3">Quick Links</h3>
                    <a
                        href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-3 py-2 text-sm text-amber-700 hover:bg-amber-50 rounded-lg transition-colors"
                    >
                        <Key size={14} />
                        OGL License
                    </a>
                </div> */}
            </aside>

            {/* Main content with left margin for sidebar */}
            <main className="pt-24 pb-16 lg:ml-56">
                {/* Hero Section */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
                            <Database size={16} />
                                API Dữ liệu Mở
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
                            Tài liệu API
                        </h1>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                            Truy cập dữ liệu hạ tầng GIS mở và cảm biến IoT theo định dạng NGSI-LD.
                            Miễn phí sử dụng theo Open Government Licence v3.0 (OGL).
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div className="flex justify-center mb-12">
                        <a
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-4 p-6 bg-white rounded-xl border border-slate-200 hover:border-amber-300 hover:shadow-lg transition-all group"
                        >
                            <div className="p-3 bg-amber-100 rounded-lg group-hover:bg-amber-200 transition-colors">
                                <Key className="text-amber-600" size={24} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-900">
                                    Open Government Licence v3.0 (OGL)
                                </h3>
                                <p className="text-sm text-slate-500">
                                    Điều khoản sử dụng
                                </p>
                            </div>
                            <ExternalLink
                                size={16}
                                className="ml-auto text-slate-400"
                            />
                        </a>
                    </div>
                </section>

                {/* License Notice */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-8">
                        <div className="flex items-start gap-4">
                            <Key
                                className="text-amber-600 shrink-0 mt-1"
                                size={24}
                            />
                            <div>
                                <h2 className="text-xl font-bold text-slate-900 mb-2">
                                    Open Government Licence v3.0 (OGL)
                                </h2>
                                <p className="text-slate-700">
                                    Data is provided free under the{" "}
                                    <a
                                        href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline font-medium"
                                    >
                                        Open Government Licence v3.0 (OGL)
                                    </a>
                                    . You are free to use, copy, distribute,
                                    transmit, and adapt the data for any
                                    purpose, including commercial use, provided
                                    you acknowledge the source.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Endpoints */}
                <section
                    id="opendata"
                    className="max-w-6xl mx-auto px-4 mb-16 scroll-mt-24"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-2 flex items-center gap-3">
                        <Code size={28} className="text-blue-600" />
                        API dữ liệu mở
                    </h2>
                    <p className="text-slate-500 mb-8">
                        Nhấn nút {" "}
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r from-[#00F2FE] to-[#4FACFE] text-white text-xs font-medium rounded">
                            <Play size={12} /> Thử
                        </span>{" "}
                        để thử ngay
                    </p>

                    <div className="space-y-4">
                        {openDataEndpoints.map((endpoint) => (
                            <EndpointCard
                                key={endpoint.path}
                                endpoint={endpoint}
                            />
                        ))}
                    </div>
                </section>

                {/* IoT NGSI-LD Section */}
                <section
                    id="iot"
                    className="max-w-6xl mx-auto px-4 mb-16 scroll-mt-24"
                >
                    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-8 mb-8">
                        <h2 className="text-2xl font-bold text-slate-900 mb-2 flex items-center gap-3">
                            <Database size={28} className="text-purple-600" />
                            Dữ liệu cảm biến IoT - NGSI-LD
                        </h2>
                        <p className="text-slate-700 mb-4">
                            Truy cập dữ liệu cảm biến IoT theo định dạng <strong>NGSI-LD</strong>{" "}
                            (chuẩn ETSI cho quản lý thông tin ngữ cảnh):
                        </p>
                        <div className="grid md:grid-cols-3 gap-4 mb-4">
                            <div className="bg-white/80 rounded-lg p-4">
                                <h4 className="font-semibold text-purple-700 mb-1">
                                    Cốt lõi NGSI-LD
                                </h4>
                                <p className="text-sm text-slate-600">
                                    Chuẩn ETSI cho các nền tảng đô thị thông minh
                                </p>
                            </div>
                            <div className="bg-white/80 rounded-lg p-4">
                                <h4 className="font-semibold text-purple-700 mb-1">
                                    Thuộc tính & Mối quan hệ
                                </h4>
                                <p className="text-sm text-slate-600">
                                    Thuộc tính có cấu trúc của thực thể
                                </p>
                            </div>
                            <div className="bg-white/80 rounded-lg p-4">
                                <h4 className="font-semibold text-purple-700 mb-1">
                                    Schema.org
                                </h4>
                                <p className="text-sm text-slate-600">
                                    Hỗ trợ từ vựng mở rộng
                                </p>
                            </div>
                        </div>
                        <p className="text-sm text-slate-600">
                            Phù hợp cho nền tảng đô thị thông minh, context broker, và khả năng tương tác IoT.
                        </p>
                    </div>

                    <div className="space-y-4">
                        {iotLinkedDataEndpoints.map((endpoint) => (
                            <EndpointCard
                                key={endpoint.path}
                                endpoint={endpoint}
                            />
                        ))}
                    </div>
                </section>

                {/* Code Examples */}
                <section
                    id="examples"
                    className="max-w-6xl mx-auto px-4 mb-16 scroll-mt-24"
                >
                    <h2 className="text-2xl font-bold text-slate-900 mb-8">
                            Ví dụ mã
                        </h2>

                    <div className="bg-slate-900 rounded-2xl overflow-hidden">
                        <div className="flex border-b border-slate-700">
                            {(["javascript", "python", "curl"] as const).map(
                                (tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`px-6 py-3 text-sm font-medium transition-colors ${
                                            activeTab === tab
                                                ? "bg-slate-800 text-white"
                                                : "text-slate-400 hover:text-white"
                                        }`}
                                    >
                                        {tab.charAt(0).toUpperCase() +
                                            tab.slice(1)}
                                    </button>
                                )
                            )}
                        </div>
                        <div className="relative p-6">
                            <div className="absolute top-2 right-2">
                                <CopyButton text={codeExamples[activeTab]} />
                            </div>
                            <pre className="text-sm text-slate-300 overflow-x-auto">
                                <code>{codeExamples[activeTab]}</code>
                            </pre>
                        </div>
                    </div>
                </section>

                {/* NGSI-LD Code Examples */}
                <section className="max-w-6xl mx-auto px-4 mb-16">
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">
                        Ví dụ NGSI-LD / Cảm biến IoT
                    </h2>
                    <p className="text-slate-600 mb-8">
                        Ví dụ minh họa cách làm việc với dữ liệu cảm biến IoT theo định dạng NGSI-LD cho tích hợp đô thị thông minh.
                    </p>

                    <div className="bg-slate-900 rounded-2xl overflow-hidden">
                        <div className="flex border-b border-slate-700">
                            {(["javascript", "python", "curl"] as const).map(
                                (tab) => (
                                    <button
                                        key={`ld-${tab}`}
                                        onClick={() => setActiveTab(tab)}
                                        className={`px-6 py-3 text-sm font-medium transition-colors ${
                                            activeTab === tab
                                                ? "bg-slate-800 text-white"
                                                : "text-slate-400 hover:text-white"
                                        }`}
                                    >
                                        {tab.charAt(0).toUpperCase() +
                                            tab.slice(1)}
                                    </button>
                                )
                            )}
                        </div>
                        <div className="relative p-6">
                            <div className="absolute top-2 right-2">
                                <CopyButton
                                    text={jsonLdCodeExamples[activeTab]}
                                />
                            </div>
                            <pre className="text-sm text-slate-300 overflow-x-auto">
                                <code>{jsonLdCodeExamples[activeTab]}</code>
                            </pre>
                        </div>
                    </div>
                </section>

                {/* MCP Server Section */}
                <section
                    id="mcp"
                    className="max-w-6xl mx-auto px-4 mb-16 scroll-mt-24"
                >
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-8 mb-8">
                        <h2 className="text-2xl font-bold text-slate-900 mb-2 flex items-center gap-3">
                            <svg
                                className="w-7 h-7 text-green-600"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                            >
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                            </svg>
                            Máy chủ MCP (Model Context Protocol)
                        </h2>
                        <p className="text-slate-700 mb-4">
                            Tích hợp dữ liệu OpenInfra trực tiếp vào trợ lý AI
                            như <strong>Claude Desktop</strong>, <strong>Cursor</strong>, hoặc bất kỳ ứng dụng tương thích MCP.
                        </p>

                        <div className="grid md:grid-cols-2 gap-6 mb-6">
                            <div className="bg-white/80 rounded-lg p-4">
                                <h4 className="font-semibold text-green-700 mb-3">
                                    🔗 URL kết nối
                                </h4>
                                <code className="block bg-slate-100 px-4 py-3 rounded-lg text-sm font-mono text-slate-800 break-all">
                                    https://mcp.openinfra.space/sse
                                </code>
                            </div>
                            <div className="bg-white/80 rounded-lg p-4">
                                <h4 className="font-semibold text-green-700 mb-3">
                                    📦 Phương thức truyền
                                </h4>
                                <p className="text-slate-600">
                                    SSE (Server-Sent Events)
                                </p>
                                <p className="text-sm text-slate-500 mt-1">
                                    Tương thích với tất cả client MCP 2.0+
                                </p>
                            </div>
                        </div>

                        <h4 className="font-semibold text-slate-800 mb-3">
                            📚 Tài nguyên sẵn có
                        </h4>
                        <div className="grid md:grid-cols-2 gap-3 mb-6">
                            <div className="bg-white/80 rounded-lg p-3">
                                <code className="text-green-700 font-mono text-sm">
                                    openapi://spec
                                </code>
                                <p className="text-sm text-slate-600 mt-1">
                                    Toàn bộ đặc tả OpenAPI
                                </p>
                            </div>
                            <div className="bg-white/80 rounded-lg p-3">
                                <code className="text-green-700 font-mono text-sm">
                                    docs://endpoints
                                </code>
                                <p className="text-sm text-slate-600 mt-1">
                                    Danh sách tất cả endpoints
                                </p>
                            </div>
                            <div className="bg-white/80 rounded-lg p-3">
                                <code className="text-green-700 font-mono text-sm">
                                    docs://opendata
                                </code>
                                <p className="text-sm text-slate-600 mt-1">
                                    Tài liệu API Dữ liệu Mở
                                </p>
                            </div>
                            <div className="bg-white/80 rounded-lg p-3">
                                <code className="text-green-700 font-mono text-sm">
                                    docs://iot
                                </code>
                                <p className="text-sm text-slate-600 mt-1">
                                    IoT Sensors API docs
                                </p>
                            </div>
                        </div>

                        <h4 className="font-semibold text-slate-800 mb-3">
                            🔧 Available Tools
                        </h4>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm bg-white/80 rounded-lg overflow-hidden">
                                <thead className="bg-green-100">
                                    <tr>
                                        <th className="text-left px-4 py-2 font-semibold text-green-800">
                                            Tool
                                        </th>
                                        <th className="text-left px-4 py-2 font-semibold text-green-800">
                                            Description
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-green-100">
                                    <tr>
                                        <td className="px-4 py-2 font-mono text-green-700">
                                            call_api
                                        </td>
                                        <td className="px-4 py-2 text-slate-600">
                                            Call any OpenInfra API endpoint
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-4 py-2 font-mono text-green-700">
                                            list_endpoints
                                        </td>
                                        <td className="px-4 py-2 text-slate-600">
                                            List all available API endpoints
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-4 py-2 font-mono text-green-700">
                                            get_feature_types
                                        </td>
                                        <td className="px-4 py-2 text-slate-600">
                                            Get infrastructure types and counts
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-4 py-2 font-mono text-green-700">
                                            get_assets
                                        </td>
                                        <td className="px-4 py-2 text-slate-600">
                                            Query assets with filters
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-4 py-2 font-mono text-green-700">
                                            get_sensors
                                        </td>
                                        <td className="px-4 py-2 text-slate-600">
                                            Query IoT sensors
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* MCP Client Configurations */}
                    <div className="space-y-4">
                        {/* Claude Desktop */}
                        <div className="bg-slate-900 rounded-2xl overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-3">
                                <svg
                                    className="w-6 h-6"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path
                                        fill="#D97757"
                                        d="M17.303 4.24c-1.403-.464-2.963-.073-4.093.993l-.166.161-.455.47-.456-.47-.165-.161c-1.131-1.066-2.69-1.457-4.094-.992C5.777 4.919 4.5 6.796 4.5 8.945c0 1.545.637 3.057 1.756 4.319C7.64 14.813 9.52 16.388 12 18.88v.002c2.48-2.493 4.36-4.068 5.744-5.616 1.119-1.262 1.756-2.774 1.756-4.319 0-2.15-1.277-4.026-3.374-4.703c-.418-.139-.857-.207-1.295-.207-.438 0-.877.068-1.294.206l-.166.162.166-.162c.417-.138.856-.206 1.294-.206.438 0 .877.068 1.295.207z"
                                    />
                                </svg>
                                <h4 className="text-white font-semibold">
                                    Claude Desktop
                                </h4>
                            </div>
                            <div className="relative p-6">
                                <p className="text-slate-400 text-sm mb-3">
                                    Add to{" "}
                                    <code className="text-blue-400">
                                        claude_desktop_config.json
                                    </code>
                                </p>
                                <div className="absolute top-2 right-2">
                                    <CopyButton
                                        text={`{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}
                                    />
                                </div>
                                <pre className="text-sm text-slate-300 overflow-x-auto bg-slate-950 p-4 rounded-lg">
                                    <code>{`{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}</code>
                                </pre>
                            </div>
                        </div>

                        {/* GitHub Copilot */}
                        <div className="bg-slate-900 rounded-2xl overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-3">
                                <svg
                                    className="w-6 h-6 text-white"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                                </svg>
                                <h4 className="text-white font-semibold">
                                    GitHub Copilot (VS Code)
                                </h4>
                            </div>
                            <div className="relative p-6">
                                <p className="text-slate-400 text-sm mb-3">
                                    Add to VS Code{" "}
                                    <code className="text-blue-400">
                                        settings.json
                                    </code>
                                </p>
                                <div className="absolute top-2 right-2">
                                    <CopyButton
                                        text={`{
  "github.copilot.chat.mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}
                                    />
                                </div>
                                <pre className="text-sm text-slate-300 overflow-x-auto bg-slate-950 p-4 rounded-lg">
                                    <code>{`{
  "github.copilot.chat.mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}</code>
                                </pre>
                            </div>
                        </div>

                        {/* Cursor */}
                        <div className="bg-slate-900 rounded-2xl overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-3">
                                <svg
                                    className="w-6 h-6"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                >
                                    <rect
                                        width="24"
                                        height="24"
                                        rx="4"
                                        fill="#1E1E1E"
                                    />
                                    <path
                                        d="M7 7h10v10H7V7z"
                                        stroke="#00D8FF"
                                        strokeWidth="2"
                                    />
                                    <circle
                                        cx="12"
                                        cy="12"
                                        r="2"
                                        fill="#00D8FF"
                                    />
                                </svg>
                                <h4 className="text-white font-semibold">
                                    Cursor
                                </h4>
                            </div>
                            <div className="relative p-6">
                                <p className="text-slate-400 text-sm mb-3">
                                    Add to MCP configuration
                                </p>
                                <div className="absolute top-2 right-2">
                                    <CopyButton
                                        text={`{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}
                                    />
                                </div>
                                <pre className="text-sm text-slate-300 overflow-x-auto bg-slate-950 p-4 rounded-lg">
                                    <code>{`{
  "mcpServers": {
    "openinfra": {
      "url": "https://mcp.openinfra.space/sse"
    }
  }
}`}</code>
                                </pre>
                            </div>
                        </div>
                    </div>
                </section>
                <section className="max-w-6xl mx-auto px-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center">
                        <h3 className="text-lg font-semibold text-slate-900 mb-2">
                            Base URL
                        </h3>
                        <code className="text-xl text-blue-600 font-mono bg-white px-4 py-2 rounded-lg border">
                            {API_BASE_URL}
                        </code>
                        <p className="text-slate-600 mt-4">
                            No API key required. Open data, free to use.
                        </p>
                    </div>
                </section>
            </main>
            <Footer />
            <AIChatWidget />
        </div>
    );
}
