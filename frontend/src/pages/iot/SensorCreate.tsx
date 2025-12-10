import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { iotApi } from "../../api/iot"
import { Form, FormField, FormLabel, FormError } from "../../components/ui/form"
import { Input } from "../../components/ui/input"
import { Select } from "../../components/ui/select"
import { Button } from "../../components/ui/button"
import { ArrowLeft } from "lucide-react"
import type { SensorCreateRequest, SensorType } from "../../types/iot"

const SensorCreate: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<Partial<SensorCreateRequest>>({
    sensor_code: "",
    asset_id: "",
    sensor_type: "temperature",
    location: {
      longitude: 0,
      latitude: 0,
    },
    measurement_unit: "",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const createMutation = useMutation({
    mutationFn: (data: SensorCreateRequest) => iotApi.createSensor(data),
    onSuccess: (sensor) => {
      queryClient.invalidateQueries({ queryKey: ["sensors"] })
      navigate({ to: `/admin/iot/${sensor.id}` })
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        // Handle FastAPI validation errors (array of objects)
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((err: any) => {
            const field = err.loc?.slice(1).join('.') || 'unknown'
            return `${field}: ${err.msg}`
          }).join('; ')
          setErrors({ submit: errorMessages })
        } else if (typeof detail === 'string') {
          setErrors({ submit: detail })
        } else {
          setErrors({ submit: 'An error occurred while creating the sensor' })
        }
      } else {
        setErrors({ submit: error.message || 'An error occurred' })
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!formData.sensor_code?.trim()) {
      setErrors({ sensor_code: "Sensor code is required" })
      return
    }
    if (!formData.asset_id?.trim()) {
      setErrors({ asset_id: "Asset ID is required" })
      return
    }

    createMutation.mutate(formData as SensorCreateRequest)
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate({ to: "/admin/iot" })}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Sensors
      </Button>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Register New Sensor</h1>

        <Form onSubmit={handleSubmit}>
          <FormField>
            <FormLabel required>Sensor Code</FormLabel>
            <Input
              value={formData.sensor_code || ""}
              onChange={(e) => setFormData({ ...formData, sensor_code: e.target.value })}
              placeholder="SENSOR-001"
            />
            {errors.sensor_code && <FormError>{errors.sensor_code}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Asset ID</FormLabel>
            <Input
              value={formData.asset_id || ""}
              onChange={(e) => setFormData({ ...formData, asset_id: e.target.value })}
              placeholder="Asset ID"
            />
            {errors.asset_id && <FormError>{errors.asset_id}</FormError>}
          </FormField>

          <FormField>
            <FormLabel required>Sensor Type</FormLabel>
            <Select
              value={formData.sensor_type || "temperature"}
              onChange={(e) => setFormData({ ...formData, sensor_type: e.target.value as SensorType })}
            >
              <option value="temperature">Temperature</option>
              <option value="humidity">Humidity</option>
              <option value="pressure">Pressure</option>
              <option value="vibration">Vibration</option>
              <option value="power">Power</option>
              <option value="voltage">Voltage</option>
              <option value="current">Current</option>
              <option value="flow_rate">Flow Rate</option>
              <option value="water_level">Water Level</option>
              <option value="air_quality">Air Quality</option>
              <option value="rainfall">Rainfall</option>
              <option value="custom">Custom</option>
            </Select>
          </FormField>

          <FormField>
            <FormLabel>Measurement Unit</FormLabel>
            <Input
              value={formData.measurement_unit || ""}
              onChange={(e) => setFormData({ ...formData, measurement_unit: e.target.value })}
              placeholder="°C, %, hPa, etc."
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FormLabel>Latitude</FormLabel>
              <Input
                type="number"
                step="any"
                value={formData.location?.latitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      latitude: parseFloat(e.target.value) || 0,
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
                value={formData.location?.longitude || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location: {
                      ...formData.location!,
                      longitude: parseFloat(e.target.value) || 0,
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
              {createMutation.isPending ? "Registering..." : "Register Sensor"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: "/admin/iot" })}
            >
              Cancel
            </Button>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default SensorCreate
