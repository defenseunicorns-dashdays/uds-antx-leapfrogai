import { HTTP } from './http';
import type { EventInformation } from './schema.ts';

const http = new HTTP();

export const Api = {
	start: () => http.get<void>('/start/'),
	update: () => http.get<EventInformation>('/update/'),
	end: () => http.get<EventInformation>('/end/')
};
