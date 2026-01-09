# github-contribution-graph-generator
flask api for quick, no-cache github contribution graph generation

## Usage:
```python
GET https://github-contribution-graph-generator.vercel.app/
gives you a status check
GET https://github-contribution-graph-generator.vercel.app/graph/<username>
generates graph and returns clean svg
USERNAME CAN ONLY BE "peme969" OR "zmushtare", ELSE IT WILL RETURN 401 ERROR 
```
