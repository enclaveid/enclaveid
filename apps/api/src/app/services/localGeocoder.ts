import geocoder from 'local-reverse-geocoder';

geocoder.init();

export function localGeocoderLookup(
  latitude: number,
  longitude: number,
): Promise<string> {
  return new Promise((resolve, reject) => {
    geocoder.lookUp({ latitude, longitude }, (error, r) => {
      if (error) {
        reject(error);
      } else {
        const result = r[0][0].name + ', ' + r[0][0].countryCode;

        resolve(result);
      }
    });
  });
}
