import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { incidentsApi } from "../../api/incidents"
import { assetsApi } from "../../api/assets"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Textarea } from "../../components/ui/textarea"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { ArrowLeft, Search, Box } from "lucide-react"
import type { IncidentCreateRequest, IncidentSeverity } from "../../types/incident"

const IncidentCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<Partial<IncidentCreateRequest>>({
    title: "",
    description: "",
    severity: "medium",
    location: {
      address: "",
      coordinates: {
        longitude: 0,
        latitude: 0,
      },
    },
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [assetSearch, setAssetSearch] = useState("")
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null)

  // Fetch assets for dropdown
  const { data: assets, isLoading: assetsLoading } = useQuery({
    queryKey: ["assets", "list"],
    queryFn: () => assetsApi.list({ limit: 500 }),
  })

  // Filter assets based on search
  const filteredAssets = assets?.filter(asset => {
    if (!assetSearch) return true
    const searchLower = assetSearch.toLowerCase()
    return (
      asset.feature_type?.toLowerCase().includes(searchLower) ||
      asset.asset_code?.toLowerCase().includes(searchLower) ||
      asset.name?.toLowerCase().includes(searchLower)
    )
  }).slice(0, 20) // Limit to 20 results

  const selectedAsset = assets?.find(a => a.id === selectedAssetId)

  const createMutation = useMutation({
    mutationFn: (data: IncidentCreateRequest) => incidentsApi.create(data),
    onSuccess: (incident) => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
      navigate({ to: `/admin/incidents/${incident.id}` })
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        setErrors({ submit: error.response.data.detail })
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.title?.trim()) {
      setErrors({ title: "Title is required" })
      return
    }
    if (!formData.description?.trim()) {
      setErrors({ description: "Description is required" })
      return
    }
    if (!formData.location?.address?.trim()) {
      setErrors({ address: "Address is required" })
      return
    }

    const submitData = {
      ...formData,
      asset_id: selectedAssetId || undefined,
      location: {
        address: formData.location?.address,
        geometry: {
          type: "Point",
          coordinates: [
            formData.location?.coordinates?.longitude || 0,
            formData.location?.coordinates?.latitude || 0,
          ],
        },
      },
    }

    createMutation.mutate(submitData as IncidentCreateRequest)
  }

  const handleAssetSelect = (assetId: string) => {
    setSelectedAssetId(assetId)
    const asset = assets?.find(a => a.id === assetId)
    if (asset) {
      // Auto-fill location from asset if available
      if (asset.geometry?.type === "Point" && asset.geometry?.coordinates) {
        setFormData(prev => ({
          ...prev,
          location: {
            ...prev.location!,
            coordinates: {
              longitude: asset.geometry.coordinates[0] as number,
              latitude: asset.geometry.coordinates[1] as number,
            },
          },
        }))
      }
    }
    setAssetSearch("")
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/incidents" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Incidents
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Report New Incident</h1>

        <Form onSubmit={handleSubmit}>
          {/* Asset Selector */}
          <FormField>
            <FormLabel>Related Asset</FormLabel>
            {selectedAsset ? (
              <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <Box className="h-5 w-5 text-blue-600" />
                <div className="flex-1">
                  <p className="font-medium text-blue-900">
                    {selectedAsset.name || selectedAsset.asset_code || selectedAsset.feature_type}
                  </p>
                  <p className="text-xs text-blue-600">{selectedAsset.feature_type}</p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedAssetId(null)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Change
                </Button>
              </div>
            ) : (
              <div className="relative">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    value={assetSearch}
                    onChange={(e) => setAssetSearch(e.target.value)}
                    placeholder="Search assets by name, code, or type..."
                    className="pl-10"
                  />
                </div>
                {assetSearch && filteredAssets && filteredAssets.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {filteredAssets.map(asset => (
                      <button
                        key={asset.id}
                        type="button"
                        onClick={() => handleAssetSelect(asset.id)}
                        className="w-full px-4 py-2 text-left hover:bg-slate-50 flex items-center gap-3 border-b border-slate-100 last:border-0"
                      >
                        <Box className="h-4 w-4 text-slate-400" />
                        <div>
                          <p className="font-medium text-sm">{asset.name || asset.asset_code || asset.feature_type}</p>
                          <p className="text-xs text-slate-500">{asset.feature_type}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
                {assetSearch && filteredAssets && filteredAssets.length === 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-4 text-center text-slate-500 text-sm">
                    No assets found matching "{assetSearch}"
                  </div>
                )}
              </div>
            )}
            <p className="text-xs text-slate-500 mt-1">
              Optional: Link this incident to a specific asset
            </p>
          </FormField>

          <FormField>
            <FormLabel required>Title</FormLabel>
            <Input
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Brief description of the incident"
            />
            {errors.title && <FormError>{errors.title}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Description</FormLabel>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Detailed description of the incident"
              rows={5}
            />
            {errors.description && <FormError>{errors.description}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Severity</FormLabel>
            <Select
              value={formData.severity || "medium"}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as IncidentSeverity })}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel required>Location Address</FormLabel>
            <Input
              value={formData.location?.address || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  location: {
                    ...formData.location!,
                    address: e.target.value,
                  },
                })
              }
              placeholder="Street address or location"
            />
            {errors.address && <FormError>{errors.address}</FormError>}
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Latitude</FormLabel>
              <Input
                type="number"
                step="any"
                value={formData.location?.coordinates?.latitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      coordinates: {
                        ...formData.location!.coordinates!,
                        latitude: parseFloat(e.target.value) || 0,
                      },
                    },
                  })
                }
                placeholder="21.0278"
              />
            </FormField>

            <FormField>
              <FormLabel>Longitude</FormLabel>
              <Input
                type="number"
                step="any"
                value={formData.location?.coordinates?.longitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      coordinates: {
                        ...formData.location!.coordinates!,
                        longitude: parseFloat(e.target.value) || 0,
                      },
                    },
                  })
                }
                placeholder="105.8342"
              />
            </FormField>
          </div>

          {errors.submit && <FormError>{errors.submit}</FormError>}

          <div className="flex gap-4 mt-6">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Incident"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/incidents" })}
            >
              Cancel
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default IncidentCreate

