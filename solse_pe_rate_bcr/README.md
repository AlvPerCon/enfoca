{
	"error":false,
	"message":false,
	"data":{
		"PD04640PD":{
			"key":"PD04640PD",
			"nombre":"Tipo de cambio - TC Sistema bancario SBS (S/ por US$) - Venta",
			"valores":{
				"2022-01-15":{
					"key":"2022-01-15",
					"formato":"%Y-%m-%d",
					"nombre":"14.Ene.22",
					"valor":3.887
				},
				"2022-01-18":{
					"key":"2022-01-18","formato":"%Y-%m-%d","nombre":"17.Ene.22","valor":3.869
				},
				"2022-01-19":{
					"key":"2022-01-19","formato":"%Y-%m-%d","nombre":"18.Ene.22","valor":3.856
				}
			}
		},
		"PD04648PD":{
			"key":"PD04648PD",
			"nombre":"Tipo de cambio - TC Euro (S/ por Euro) - Venta",
			"valores":{
				"2022-01-15":{
					"key":"2022-01-15","formato":"%Y-%m-%d","nombre":"14.Ene.22","valor":4.536
				},
				"2022-01-18":{
					"key":"2022-01-18","formato":"%Y-%m-%d","nombre":"17.Ene.22","valor":4.764
				},
				"2022-01-19":{
					"key":"2022-01-19","formato":"%Y-%m-%d","nombre":"18.Ene.22","valor":4.565
				}
			}
		}
	}
}

# por apidev
{"success":true,"data":{"fecha_busqueda":"2021-12-02","fecha_sunat":"2021-12-02","venta":4.071,"compra":4.061},"source":"apiperu.dev"}

import requests
endpoint = "https://apiperu.dev/api/tipo_de_cambio?fecha=2021-12-02"
token = 'd1972aef5d49b955acb719ed9f13c3dfda2eb8befe7ba4167a7978176501e1b5'
headers = {
	"Authorization": "Bearer %s" % token,
	"Content-Type": "application/json",
}
datos_consultar = {
	"fecha": "20201-12-02",
}
datos_request = requests.post(url=endpoint, data=datos_consultar, headers=headers)
datos_request.text