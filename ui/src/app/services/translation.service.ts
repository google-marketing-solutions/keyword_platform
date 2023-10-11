/**
 * @license
 * Copyright 2023 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {Inject, Injectable} from '@angular/core';
import {Language} from '../models/interfaces';
import {HttpClient, HttpErrorResponse, HttpHeaders, HttpParams, HttpResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {catchError, map} from 'rxjs/operators';
import {LOCATION_TOKEN} from '../shared/tokens';

/** Translation service. */
@Injectable({providedIn: 'root'})
export class TranslationService {
  constructor(
    private readonly http: HttpClient,
    @Inject(LOCATION_TOKEN) private readonly location: Location) {}

  getGlossaries(): Observable<HttpResponse<string[]>> {
    const params =
        new HttpParams({fromObject: {'endpoint': 'list_glossaries'}});
    return this.http
        .get<string[]>(
            this.getHost('list_glossaries'),
            {
              headers: this.getHeader(),
              observe: 'response',
              params,
              responseType: 'json'
            },
            )
        .pipe(catchError(this.handleError), map(response => response));
  }

  // TODO(): Consider obtaining list of languages from the
  // Cloud Translation API, a Keyword Platform endpoint (if in the roadmap)
  // or a JSON file.
  getLanguages(): Language[] {
    return [
      {code: 'af', name: 'Afrikaans'},
      {code: 'ak', name: 'Akan'},
      {code: 'sq', name: 'Albanian'},
      {code: 'am', name: 'Amharic'},
      {code: 'ar', name: 'Arabic'},
      {code: 'hy', name: 'Armenian'},
      {code: 'as', name: 'Assamese'},
      {code: 'ay', name: 'Aymara'},
      {code: 'az', name: 'Azerbaijani'},
      {code: 'bm', name: 'Bambara'},
      {code: 'eu', name: 'Basque'},
      {code: 'be', name: 'Belarusian'},
      {code: 'bn', name: 'Bengali'},
      {code: 'bho', name: 'Bhojpuri'},
      {code: 'bs', name: 'Bosnian'},
      {code: 'bg', name: 'Bulgarian'},
      {code: 'ca', name: 'Batalan'},
      {code: 'ceb', name: 'Cebuano'},
      {code: 'ny', name: 'Chichewa'},
      // TODO(): Confirm version of language.
      // {code: 'zh', name: 'Chinese (simplified)'},
      {code: 'zh_cn', name: 'Chinese (simplified)'},
      {code: 'zh_tw', name: 'Chinese (traditional)'},
      {code: 'co', name: 'Corsican'},
      {code: 'hr', name: 'Croatian'},
      {code: 'cs', name: 'Czech'},
      {code: 'da', name: 'Danish'},
      {code: 'dv', name: 'Divehi'},
      {code: 'doi', name: 'Dogri'},
      {code: 'nl', name: 'Dutch'},
      {code: 'en', name: 'English'},
      {code: 'eo', name: 'Esperanto'},
      {code: 'et', name: 'Estonian'},
      {code: 'ee', name: 'Ewe'},
      {code: 'tl', name: 'Filipino'},
      {code: 'fi', name: 'Finnish'},
      {code: 'fr', name: 'French'},
      {code: 'fy', name: 'Frisian'},
      {code: 'gl', name: 'Galician'},
      {code: 'lg', name: 'Ganda'},
      {code: 'ka', name: 'Georgian'},
      {code: 'de', name: 'German'},
      {code: 'gom', name: 'Goan konkani'},
      {code: 'el', name: 'Greek'},
      {code: 'gn', name: 'Guarani'},
      {code: 'gu', name: 'Gujarati'},
      {code: 'ht', name: 'Haitian creole'},
      {code: 'ha', name: 'Hausa'},
      {code: 'haw', name: 'Hawaiian'},
      // TODO(): Confirm version of language.
      // {code: 'iw', name: 'Hebrew'},
      {code: 'he', name: 'Hebrew'},
      {code: 'hi', name: 'Hindi'},
      {code: 'hmn', name: 'Hmong'},
      {code: 'hu', name: 'Hungarian'},
      {code: 'is', name: 'Icelandic'},
      {code: 'ig', name: 'Igbo'},
      {code: 'ilo', name: 'Iloko'},
      {code: 'id', name: 'Indonesian'},
      {code: 'ga', name: 'Irish'},
      {code: 'it', name: 'Italian'},
      {code: 'ja', name: 'Japanese'},
      // TODO(): Confirm version of language.
      // {code: 'jw', name: 'Javanese'},
      {code: 'jv', name: 'Javanese'},
      {code: 'kn', name: 'Kannada'},
      {code: 'kk', name: 'Kazakh'},
      {code: 'km', name: 'Khmer'},
      {code: 'rw', name: 'Kinyarwanda'},
      {code: 'ko', name: 'Korean'},
      {code: 'kri', name: 'Krio'},
      {code: 'ku', name: 'Kurdish (kurmanji)'},
      {code: 'ckb', name: 'Kurdish (sorani)'},
      {code: 'ky', name: 'Kyrgyz'},
      {code: 'lo', name: 'Lao'},
      {code: 'la', name: 'Latin'},
      {code: 'lv', name: 'Latvian'},
      {code: 'ln', name: 'Lingala'},
      {code: 'lt', name: 'Lithuanian'},
      {code: 'lb', name: 'Luxembourgish'},
      {code: 'mk', name: 'Macedonian'},
      {code: 'mai', name: 'Maithili'},
      {code: 'mg', name: 'Malagasy'},
      {code: 'ms', name: 'Malay'},
      {code: 'ml', name: 'Malayalam'},
      {code: 'mt', name: 'Maltese'},
      {code: 'mni_mtei', name: 'Manipuri (Meitei Mayek)'},
      {code: 'mi', name: 'Maori'},
      {code: 'mr', name: 'Marathi'},
      {code: 'lus', name: 'Mizo'},
      {code: 'mn', name: 'Mongolian'},
      {code: 'my', name: 'Myanmar (burmese)'},
      {code: 'ne', name: 'Nepali'},
      {code: 'nso', name: 'Northern sotho'},
      {code: 'no', name: 'Norwegian'},
      {code: 'or', name: 'Odia (oriya)'},
      {code: 'om', name: 'Oromo'},
      {code: 'ps', name: 'Pashto'},
      {code: 'fa', name: 'Persian'},
      {code: 'pl', name: 'Polish'},
      {code: 'pt', name: 'Portuguese'},
      {code: 'pa', name: 'Punjabi'},
      {code: 'qu', name: 'Quechua'},
      {code: 'ro', name: 'Romanian'},
      {code: 'ru', name: 'Russian'},
      {code: 'sm', name: 'Samoan'},
      {code: 'sa', name: 'Sanskrit'},
      {code: 'gd', name: 'Scots gaelic'},
      {code: 'sr', name: 'Serbian'},
      {code: 'st', name: 'Sesotho'},
      {code: 'sn', name: 'Shona'},
      {code: 'sd', name: 'Sindhi'},
      {code: 'si', name: 'Sinhala'},
      {code: 'sk', name: 'Slovak'},
      {code: 'sl', name: 'Slovenian'},
      {code: 'so', name: 'Somali'},
      {code: 'es', name: 'Spanish'},
      {code: 'su', name: 'Sundanese'},
      {code: 'sw', name: 'Swahili'},
      {code: 'sv', name: 'Swedish'},
      {code: 'tg', name: 'Tajik'},
      {code: 'ta', name: 'Tamil'},
      {code: 'tt', name: 'Tatar'},
      {code: 'te', name: 'Telugu'},
      {code: 'th', name: 'Thai'},
      {code: 'ti', name: 'Tigrinya'},
      {code: 'ts', name: 'Tsonga'},
      {code: 'tr', name: 'Turkish'},
      {code: 'tk', name: 'Turkmen'},
      {code: 'uk', name: 'Ukrainian'},
      {code: 'ur', name: 'Urdu'},
      {code: 'ug', name: 'Uyghur'},
      {code: 'uz', name: 'Uzbek'},
      {code: 'vi', name: 'Vietnamese'},
      {code: 'cy', name: 'Welsh'},
      {code: 'xh', name: 'Xhosa'},
      {code: 'yi', name: 'Yiddish'},
      {code: 'yo', name: 'Yoruba'},
      {code: 'zu', name: 'Zulu'}
    ];
  }

  private handleError(error: HttpErrorResponse) {
    return throwError(error.message);
  }

  private getHeader() {
    return new HttpHeaders({'Content-Type': 'application/json'});
  }

  private getHost(api: string) {
    return (
        this.location.hostname === 'localhost' ? './test-api/' + api + '.json' :
                                                 './proxy');
  }
}
