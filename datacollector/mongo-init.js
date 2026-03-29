db = db.getSiblingDB('openinfra_gis');

db.createUser({
  user: 'mongodb_admin',
  pwd: 'HlVUAfrS3ZtneygGWWakWvfEPDlNhLQ8',
  roles: [
    {
      role: 'readWrite',
      db: 'openinfra_gis'
    }
  ]
});
