# Water Observatory Backend

This repository shows how the [BlueDot](https://www.blue-dot-observatory.com)'s Water Observatory is extracting surface water levels of waterbodies across the globe. The algorithm is described in more details [here](https://www.blue-dot-observatory.com/aboutwaterobservatory).

An [example Jupyter notebook](https://github.com/sentinel-hub/water-observatory-backend/blob/master/example/example-optical-water-level-extraction.ipynb) shows how to extract surface water level for a single dam on a specific date. The Bluedot's Water Observatory repeats this operation for all monitored waterbodies and for all available Sentinel-2 imagery and uploads the results to S3 which is used by the dashboard to display the results. 
The results are presented in [BlueDot Water Observatory Dashboard](https://water.blue-dot-observatory.com/38419). Frontend application is available 
in this [repository](https://github.com/sentinel-hub/water-observatory-frontend). 

## Blogs and papers

* [Global earth observation service from your laptop](https://medium.com/sentinel-hub/global-earth-observation-service-from-your-laptop-23157680cf5e)
* [BLUEDOT - Water Resource Monitoring from Space](https://medium.com/sentinel-hub/bluedot-eo-solution-for-water-resources-monitoring-d7663c21af16)
* [BlueDot Observatory – keeping an eye on our planet’s water resources](https://aws.amazon.com/blogs/publicsector/bluedot-observatory-keeping-an-eye-on-our-planets-water-resources/) - Amazon Web Services Government, Education, & Nonprofits Blog
* [Bluedot water observatory - Cost effective near real time monitoring of global water resources]((https://www.researchgate.net/publication/333262569_Bluedot_water_observatory_-_Cost_effective_near_real_time_monitoring_of_global_water_resources)by Anze Zupanc)

## Twitter

Follow us on Twitter: [@BlueDotObs](https://twitter.com/BlueDotObs). 

## License

See [LICENSE](LICENSE).
