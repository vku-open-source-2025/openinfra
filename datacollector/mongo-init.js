// App user for the GISTool backend. Credentials come from the container
// environment (compose `.env`), never from this file.
const user = (typeof process !== 'undefined' && process.env.MONGO_USERNAME) || 'mongodb_admin';
const pwd = (typeof process !== 'undefined' && process.env.MONGO_PASSWORD) || '';
if (pwd) {
  db = db.getSiblingDB('openinfra_gis');
  try {
    db.createUser({ user, pwd, roles: [{ role: 'readWrite', db: 'openinfra_gis' }] });
  } catch (e) {
    print('user already exists: ' + e.message);
  }
}
